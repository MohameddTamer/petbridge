// The home screen must make the customer's world obvious:
// pets, due items, and the quick actions, all on one page.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petbridge_client/models.dart';
import 'package:petbridge_client/screens/home_screen.dart';
import 'package:petbridge_client/state.dart';

void main() {
  testWidgets('home shows pets, due items and quick actions',
      (tester) async {
    final state = AppState();
    state.pets = [
      Pet(
        id: 1,
        name: 'Roki',
        species: 'dog',
        breed: 'Baladi',
        birthDate: '2022-01-01',
        ageLabel: '4 years',
        sex: 'male',
        weightKg: 18,
        notes: '',
        healthRecords: [
          HealthRecord(
            id: 1,
            kind: 'vaccine',
            name: 'Rabies',
            givenDate: '2025-01-01',
            nextDue: '2020-01-01',
            status: 'overdue',
            providerName: 'Clinic',
          ),
        ],
      ),
    ];
    state.due = [
      {
        'pet_name': 'Roki',
        'name': 'Rabies',
        'next_due': '2020-01-01',
        'status': 'overdue',
      },
    ];
    state.tourDone = true;
    state.signedIn = true;

    await tester.pumpWidget(
      MaterialApp(
        home: HomeScreen(
          state: state,
          onPet: (_) {},
          onServices: () {},
          onLostFound: () {},
          onBreed: () {},
          onSignOut: () {},
        ),
      ),
    );
    // Home loads from the network; the seeded state renders after the
    // failed refresh settles. Pump until the page stops changing.
    await tester.pump(const Duration(seconds: 1));
    expect(find.text('Your pets'), findsOneWidget);
    expect(find.text('Roki'), findsWidgets);
    expect(find.text('Due soon or overdue'), findsOneWidget);
    expect(find.text('Quick actions'), findsOneWidget);
    expect(find.text('Browse services'), findsOneWidget);
    expect(find.text('Breed ID (beta)'), findsOneWidget);
  });
}
