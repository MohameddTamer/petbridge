// One pet page: details on top, health timeline below on a dashed
// stitch line. Dots fill ochre when due soon, brick when overdue.
import 'package:flutter/material.dart';
import '../api.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets/drawn.dart';

class PetScreen extends StatefulWidget {
  final ApiClient api;
  final Pet pet;
  const PetScreen({super.key, required this.api, required this.pet});
  @override
  State<PetScreen> createState() => _PetScreenState();
}

class _PetScreenState extends State<PetScreen> {
  late Pet _pet;
  final _recordName = TextEditingController();
  final _given = TextEditingController();
  final _nextDue = TextEditingController();
  String? _error;

  @override
  void initState() {
    super.initState();
    _pet = widget.pet;
  }

  Future<void> _addRecord() async {
    try {
      final record = await widget.api.addHealthRecord(_pet.id, {
        'kind': 'checkup',
        'name': _recordName.text.trim(),
        'given_date': _given.text.trim(),
        'next_due': _nextDue.text.trim().isEmpty ? null : _nextDue.text.trim(),
      });
      setState(() {
        _pet = Pet(
          id: _pet.id,
          name: _pet.name,
          species: _pet.species,
          breed: _pet.breed,
          birthDate: _pet.birthDate,
          ageLabel: _pet.ageLabel,
          sex: _pet.sex,
          weightKg: _pet.weightKg,
          notes: _pet.notes,
          healthRecords: [..._pet.healthRecords, record],
        );
        _recordName.clear();
        _given.clear();
        _nextDue.clear();
        _error = null;
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          title: Text(_pet.name),
          backgroundColor: PbColors.paper,
          foregroundColor: PbColors.ink,
          elevation: 0),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('${_pet.species} · ${_pet.breed}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          Text('Born ${_pet.birthDate} · ${_pet.ageLabel}'
              '${_pet.weightKg != null ? ' · ${_pet.weightKg} kg' : ''}'),
          if (_pet.notes.isNotEmpty) Text(_pet.notes),
          const SizedBox(height: 24),
          const Text('Health timeline',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
          if (_pet.healthRecords.isEmpty)
            const Text('No health records yet.'),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              StitchLine(
                  height: (_pet.healthRecords.length * 76).toDouble(),
                  color: PbColors.teal),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  children: _pet.healthRecords.map((r) {
                    final color = r.status == 'overdue'
                        ? PbColors.brick
                        : r.status == 'due_soon'
                            ? PbColors.ochre
                            : PbColors.teal;
                    return Container(
                      margin: const EdgeInsets.only(bottom: 14),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        border: Border.all(color: PbColors.ink, width: 1),
                        borderRadius: handCutRadius(),
                      ),
                      child: Row(
                        children: [
                          Container(
                              width: 12,
                              height: 12,
                              decoration: BoxDecoration(
                                  color: color, shape: BoxShape.circle)),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(r.name,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700)),
                                Text(
                                    'Given ${r.givenDate}${r.nextDue != null ? ' · next due ${r.nextDue}' : ''} · ${r.status}'),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          const Text('Add a health record',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          TextField(
              controller: _recordName,
              decoration: const InputDecoration(labelText: 'Record name')),
          const SizedBox(height: 8),
          TextField(
              controller: _given,
              decoration:
                  const InputDecoration(labelText: 'Given date (YYYY-MM-DD)')),
          const SizedBox(height: 8),
          TextField(
              controller: _nextDue,
              decoration: const InputDecoration(
                  labelText: 'Next due (YYYY-MM-DD, optional)')),
          if (_error != null)
            Text(_error!, style: const TextStyle(color: PbColors.brick)),
          const SizedBox(height: 12),
          ElevatedButton(onPressed: _addRecord, child: const Text('Save record')),
        ],
      ),
    );
  }
}
