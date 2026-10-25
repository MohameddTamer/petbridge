// The customer home: pets first, due items next, quick actions last.
// The first run shows a short guided tour before the page settles.
import 'package:flutter/material.dart';
import '../models.dart';
import '../money.dart';
import '../state.dart';
import '../theme.dart';
import '../widgets/drawn.dart';

class HomeScreen extends StatefulWidget {
  final AppState state;
  final void Function(Pet pet) onPet;
  final VoidCallback onServices;
  final VoidCallback onLostFound;
  final VoidCallback onBreed;
  final VoidCallback onSignOut;
  const HomeScreen({
    super.key,
    required this.state,
    required this.onPet,
    required this.onServices,
    required this.onLostFound,
    required this.onBreed,
    required this.onSignOut,
  });
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    widget.state.refreshHome();
    if (!widget.state.tourDone) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _tour());
    }
  }

  Future<void> _tour() async {
    widget.state.tourDone = true;
    const steps = [
      'Welcome to PetBridge. This page is your notebook.',
      'Your pets live here as taped pages. Tap one to see its health timeline.',
      'Due items are stitched in ochre when soon, brick when overdue.',
      'Quick actions below take you to services, bookings, lost pets and breed ID.',
    ];
    for (final step in steps) {
      if (!mounted) return;
      final next = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: const Text('A quick tour'),
          content: Text(step),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Skip tour')),
            ElevatedButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Next')),
          ],
        ),
      );
      if (next != true) break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    return Scaffold(
      appBar: AppBar(
        title: const Text('PetBridge'),
        backgroundColor: PbColors.paper,
        foregroundColor: PbColors.ink,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign out',
            onPressed: () {
              state.signOut();
              widget.onSignOut();
            },
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: state,
        builder: (context, _) {
          if (state.homeError != null &&
              state.pets.isEmpty &&
              state.due.isEmpty) {
            return Center(child: Text(state.homeError!));
          }
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              if (state.homeError != null)
                Text('Could not refresh: ${state.homeError!}',
                    style: const TextStyle(color: PbColors.brick)),
              const Text('Good to see you again.',
                  style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                      color: PbColors.ink)),
              const Text(
                  'Everything your pets need, in one notebook.',
                  style: TextStyle(fontSize: 15, color: PbColors.ink)),
              const SizedBox(height: 8),
              const PawTrail(),
              const SizedBox(height: 20),
              const Text('Your pets', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
              const SizedBox(height: 10),
              if (state.pets.isEmpty)
                const Text(
                    'No pets yet. Add one from the pet page after signing in.'),
              for (var i = 0; i < state.pets.length; i++)
                _PetPage(
                  pet: state.pets[i],
                  tapeColor: i.isEven ? PbColors.teal : PbColors.ochre,
                  onTap: () => widget.onPet(state.pets[i]),
                ),
              const SizedBox(height: 24),
              const Text('Due soon or overdue',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
              const SizedBox(height: 10),
              if (state.due.isEmpty)
                const Text('Nothing due. A quiet notebook is a healthy one.'),
              for (final item in state.due) _DueRow(item: item),
              const SizedBox(height: 24),
              const Text('Quick actions',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
              const SizedBox(height: 10),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  _Action('Browse services', Icons.search, widget.onServices),
                  _Action('Lost and found', Icons.pets, widget.onLostFound),
                  _Action('Breed ID (beta)', Icons.camera_alt, widget.onBreed),
                ],
              ),
              const SizedBox(height: 24),
              const Text('Recent bookings',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
              for (final b in state.bookings)
                ListTile(
                  title: Text('${b.serviceName} at ${b.businessName}'),
                  subtitle: Text('${b.startAt}, ${b.status}'),
                  trailing: Text(egp(b.total),
                      style: const TextStyle(fontWeight: FontWeight.w700)),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _PetPage extends StatelessWidget {
  final Pet pet;
  final Color tapeColor;
  final VoidCallback onTap;
  const _PetPage(
      {required this.pet, required this.tapeColor, required this.onTap});
  @override
  Widget build(BuildContext context) {
    final dueCount = pet.dueItems.length;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(18, 26, 18, 16),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(color: PbColors.ink, width: 1.2),
                borderRadius: handCutRadius(),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(pet.name,
                      style: const TextStyle(
                          fontSize: 20, fontWeight: FontWeight.w800)),
                  Text('${pet.species} · ${pet.breed} · ${pet.ageLabel}'),
                  if (dueCount > 0)
                    Text('$dueCount item${dueCount == 1 ? '' : 's'} due',
                        style: const TextStyle(
                            color: PbColors.brick,
                            fontWeight: FontWeight.w700)),
                ],
              ),
            ),
            Positioned(
              top: -10,
              left: 32,
              child: WashiTape(color: tapeColor),
            ),
          ],
        ),
      ),
    );
  }
}

class _DueRow extends StatelessWidget {
  final Map<String, dynamic> item;
  const _DueRow({required this.item});
  @override
  Widget build(BuildContext context) {
    final overdue = item['status'] == 'overdue';
    return ListTile(
      leading: Icon(Icons.medical_services,
          color: overdue ? PbColors.brick : PbColors.ochre),
      title: Text('${item['pet_name']}: ${item['name']}'),
      subtitle: Text('Due ${item['next_due'] ?? ''}'),
      trailing: Text(overdue ? 'Overdue' : 'Due soon',
          style: TextStyle(
              color: overdue ? PbColors.brick : PbColors.deepTeal,
              fontWeight: FontWeight.w700)),
    );
  }
}

class _Action extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;
  const _Action(this.label, this.icon, this.onTap);
  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 18),
      label: Text(label),
    );
  }
}
