// The directory: all 35 services in 8 categories, with real prices
// from approved providers. Category chips filter; search narrows further.
import 'package:flutter/material.dart';
import '../api.dart';
import '../models.dart';
import '../money.dart';
import '../theme.dart';

class ServicesScreen extends StatefulWidget {
  final ApiClient api;
  final void Function(ProviderEntry provider, DirectoryService service) onBook;
  const ServicesScreen({super.key, required this.api, required this.onBook});
  @override
  State<ServicesScreen> createState() => _ServicesScreenState();
}

class _ServicesScreenState extends State<ServicesScreen> {
  List<TaxonomyCategory> _categories = [];
  List<ProviderEntry> _providers = [];
  String _category = '';
  String _query = '';
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final cats = await widget.api.taxonomy();
      final providers =
          await widget.api.directory(category: _category, query: _query);
      if (!mounted) return;
      setState(() {
        _categories = cats;
        _providers = providers;
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
    return Scaffold(
      appBar: AppBar(
          title: const Text('Services'),
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
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: TextField(
                        decoration: const InputDecoration(
                            labelText: 'Search services or providers'),
                        onChanged: (v) {
                          _query = v;
                          _load();
                        },
                      ),
                    ),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          ChoiceChip(
                            label: const Text('All services'),
                            selected: _category.isEmpty,
                            onSelected: (_) {
                              _category = '';
                              _load();
                            },
                          ),
                          for (final c in _categories)
                            Padding(
                              padding: const EdgeInsets.only(left: 8),
                              child: ChoiceChip(
                                label: Text(c.label),
                                selected: _category == c.key,
                                onSelected: (_) {
                                  _category = c.key;
                                  _load();
                                },
                              ),
                            ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          for (final p in _providers) ...[
                            Text(p.businessName,
                                style: const TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.w800)),
                            Text('${p.city} · ${p.area}'),
                            for (final s in p.services)
                              ListTile(
                                title: Text(s.name),
                                subtitle: Text(
                                    '${s.categoryLabel} · ${s.durationMin} min · ${s.mode}'),
                                trailing: Text(egp(s.price),
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700)),
                                onTap: () => widget.onBook(p, s),
                              ),
                            const Divider(),
                          ],
                          if (_providers.isEmpty)
                            const Text(
                                'No approved services match that filter yet.'),
                        ],
                      ),
                    ),
                  ],
                ),
    );
  }
}
