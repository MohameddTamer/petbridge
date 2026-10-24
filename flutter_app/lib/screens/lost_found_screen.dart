// Lost-and-found browsing, open to guests too.
// Reports are filed on the website for now; this screen reads them.
import 'package:flutter/material.dart';
import '../api.dart';
import '../models.dart';
import '../theme.dart';

class LostFoundScreen extends StatefulWidget {
  final ApiClient api;
  const LostFoundScreen({super.key, required this.api});
  @override
  State<LostFoundScreen> createState() => _LostFoundScreenState();
}

class _LostFoundScreenState extends State<LostFoundScreen> {
  List<LostItem> _items = [];
  String _filter = 'all';
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final items = await widget.api.lostFound();
      if (!mounted) return;
      setState(() {
        _items = items;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final shown = _filter == 'all'
        ? _items
        : _items.where((i) => i.kind == _filter).toList();
    return Scaffold(
      appBar: AppBar(
          title: const Text('Lost and found'),
          backgroundColor: PbColors.paper,
          foregroundColor: PbColors.ink,
          elevation: 0),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(value: 'all', label: Text('All')),
                          ButtonSegment(value: 'lost', label: Text('Lost')),
                          ButtonSegment(value: 'found', label: Text('Found')),
                        ],
                        selected: {_filter},
                        onSelectionChanged: (s) =>
                            setState(() => _filter = s.first),
                      ),
                    ),
                    Expanded(
                      child: ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          for (final item in shown)
                            Container(
                              margin: const EdgeInsets.only(bottom: 14),
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                border: Border.all(
                                    color: PbColors.ink, width: 1),
                                borderRadius: handCutRadius(),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(item.title,
                                      style: const TextStyle(
                                          fontSize: 17,
                                          fontWeight: FontWeight.w800)),
                                  Text(
                                      '${item.kind == 'lost' ? 'Lost' : 'Found'} · ${item.petName} · ${item.species} · ${item.city} ${item.area}'),
                                  if (item.description.isNotEmpty)
                                    Text(item.description),
                                  Text('Posted by ${item.authorName} · ${item.status}'),
                                ],
                              ),
                            ),
                          if (shown.isEmpty)
                            const Text('Nothing here yet.'),
                        ],
                      ),
                    ),
                  ],
                ),
    );
  }
}
