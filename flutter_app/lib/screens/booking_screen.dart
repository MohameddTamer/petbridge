// Service detail plus the booking flow.
// The preview splits price with the same math as the backend, and the
// confirmation shows the exact figures the backend returned.
import 'package:flutter/material.dart';
import '../api.dart';
import '../models.dart';
import '../money.dart';
import '../state.dart';
import '../theme.dart';
import '../widgets/drawn.dart';

class BookingScreen extends StatefulWidget {
  final AppState state;
  final ProviderEntry provider;
  final DirectoryService service;
  const BookingScreen({
    super.key,
    required this.state,
    required this.provider,
    required this.service,
  });
  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  int? _petId;
  int? _slotId;
  final _startAt = TextEditingController();
  final _notes = TextEditingController();
  Booking? _done;
  String? _error;
  bool _busy = false;
  static const double standardRate = 0.12;

  Future<void> _book() async {
    if (_slotId == null && _startAt.text.trim().isEmpty) {
      setState(() => _error = 'Pick a slot or set a start time.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final booking = await widget.state.api.createBooking(
        serviceId: widget.service.id,
        petId: _petId,
        slotId: _slotId,
        startAt: _slotId == null ? _startAt.text.trim() : null,
        notes: _notes.text,
      );
      setState(() => _done = booking);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final service = widget.service;
    final (previewCommission, previewNet) =
        splitBooking(service.price, standardRate);
    return Scaffold(
      appBar: AppBar(
          title: Text(service.name),
          backgroundColor: PbColors.paper,
          foregroundColor: PbColors.ink,
          elevation: 0),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(widget.provider.businessName,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          Text(
              '${service.categoryLabel} · ${service.durationMin} min · ${service.mode}'),
          const SizedBox(height: 16),
          _MoneyRow('Price', egp(service.price)),
          _MoneyRow('Platform commission (12%)', egp(previewCommission)),
          _MoneyRow('Provider receives', egp(previewNet)),
          const Text(
              'The commission shown is the standard 12% rate. The booking confirmation below shows the exact figures the server recorded.',
              style: TextStyle(fontSize: 13)),
          const SizedBox(height: 20),
          if (_done == null) ...[
            if (widget.state.pets.isNotEmpty)
              DropdownButtonFormField<int>(
                decoration: const InputDecoration(labelText: 'Pet (optional)'),
                items: widget.state.pets
                    .map((p) => DropdownMenuItem(value: p.id, child: Text(p.name)))
                    .toList(),
                onChanged: (v) => setState(() => _petId = v),
              ),
            if (service.slots.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('Available slots',
                  style: TextStyle(fontWeight: FontWeight.w700)),
              RadioGroup<int>(
                groupValue: _slotId,
                onChanged: (v) => setState(() => _slotId = v),
                child: Column(
                  children: [
                    for (final slot in service.slots)
                      RadioListTile<int>(
                        title: Text(
                            '${slot.date} ${slot.startTime} to ${slot.endTime}'),
                        subtitle: Text('${slot.remaining} places left'),
                        value: slot.id,
                      ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 12),
            TextField(
                controller: _startAt,
                decoration: const InputDecoration(
                    labelText: 'Or start time (e.g. 2026-11-02T10:00:00)')),
            const SizedBox(height: 12),
            TextField(
                controller: _notes,
                decoration: const InputDecoration(labelText: 'Notes')),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: PbColors.brick)),
            ],
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _busy ? null : _book,
                child: const Text('Send booking request'),
              ),
            ),
          ] else ...[
            const SizedBox(height: 12),
            const Center(child: CircledText('Booking sent')),
            const SizedBox(height: 12),
            const Text('A note in the margin: your request is with the provider now.',
                textAlign: TextAlign.center),
            const SizedBox(height: 16),
            _MoneyRow('Total charged', egp(_done!.total)),
            _MoneyRow(
                'Commission (${(_done!.commissionRate * 100).toStringAsFixed(0)}%)',
                egp(_done!.commission)),
            _MoneyRow('Provider net', egp(_done!.providerNet)),
            Text('Status: ${_done!.status} · ${_done!.paymentLabel}'),
          ],
        ],
      ),
    );
  }
}

class _MoneyRow extends StatelessWidget {
  final String label;
  final String value;
  const _MoneyRow(this.label, this.value);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
