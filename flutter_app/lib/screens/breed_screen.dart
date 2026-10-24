// Breed ID entry point, calling the real backend beta endpoint.
// Results are labelled beta everywhere, with the backend note shown
// in full. No accuracy claim is made anywhere on this screen.
import 'package:flutter/material.dart';
import '../api.dart';
import '../models.dart';
import '../theme.dart';

class BreedScreen extends StatefulWidget {
  final ApiClient api;
  const BreedScreen({super.key, required this.api});
  @override
  State<BreedScreen> createState() => _BreedScreenState();
}

class _BreedScreenState extends State<BreedScreen> {
  final _fileName = TextEditingController(text: 'pet-photo.jpg');
  String _species = 'dog';
  BreedResult? _result;
  String? _error;
  bool _busy = false;

  Future<void> _analyze() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await widget.api
          .breedAnalyze(fileName: _fileName.text.trim(), species: _species);
      setState(() => _result = result);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          title: const Text('Breed ID'),
          backgroundColor: PbColors.paper,
          foregroundColor: PbColors.ink,
          elevation: 0),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: PbColors.softOchre,
              border: Border.all(color: PbColors.ochre),
              borderRadius: handCutRadius(),
            ),
            child: const Text(
                'Beta. This identification is a demo flow and carries no accuracy rate. Confirming breed and health needs a vet, or a real vision model at launch.'),
          ),
          const SizedBox(height: 20),
          TextField(
              controller: _fileName,
              decoration: const InputDecoration(
                  labelText: 'Photo file name (e.g. roki-baladi.jpg)')),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _species,
            decoration:
                const InputDecoration(labelText: 'Declared species'),
            items: const [
              DropdownMenuItem(value: 'dog', child: Text('Dog')),
              DropdownMenuItem(value: 'cat', child: Text('Cat')),
              DropdownMenuItem(value: 'other', child: Text('Other')),
            ],
            onChanged: (v) => setState(() => _species = v ?? 'other'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: PbColors.brick)),
          ],
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _busy ? null : _analyze,
              child: const Text('Identify (beta)'),
            ),
          ),
          if (_result != null) ...[
            const SizedBox(height: 24),
            Text(_result!.breed,
                style: const TextStyle(
                    fontSize: 24, fontWeight: FontWeight.w800)),
            Text('${_result!.species} · ${_result!.label}'),
            const SizedBox(height: 8),
            Text(_result!.summary),
            const SizedBox(height: 8),
            Text('Care: ${_result!.care}'),
            const SizedBox(height: 8),
            Text(_result!.note,
                style: const TextStyle(fontStyle: FontStyle.italic)),
          ],
        ],
      ),
    );
  }
}
