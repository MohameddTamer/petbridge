// API parsing must follow the backend JSON shapes.
import 'package:flutter_test/flutter_test.dart';
import 'package:petbridge_client/models.dart';

void main() {
  test('pet parses with its health timeline and due filter', () {
    final pet = Pet.fromJson({
      'id': 1,
      'name': 'Roki',
      'species': 'dog',
      'breed': 'Baladi',
      'birth_date': '2022-01-01',
      'age_label': '4 years',
      'sex': 'male',
      'weight_kg': 18,
      'notes': '',
      'health_records': [
        {
          'id': 1,
          'kind': 'vaccine',
          'name': 'Rabies',
          'given_date': '2025-01-01',
          'next_due': '2020-01-01',
          'status': 'overdue',
          'provider_name': 'Clinic',
        },
        {
          'id': 2,
          'kind': 'checkup',
          'name': 'Annual check',
          'given_date': '2025-06-01',
          'next_due': '2099-01-01',
          'status': 'ok',
          'provider_name': 'Clinic',
        },
      ],
    });
    expect(pet.name, 'Roki');
    expect(pet.dueItems.length, 1);
    expect(pet.dueItems.first.name, 'Rabies');
  });

  test('booking parses the money fields the backend records', () {
    final booking = Booking.fromJson({
      'id': 3,
      'business_name': 'Cairo Vet',
      'service_name': 'General checkup',
      'pet_name': 'Roki',
      'start_at': '2026-11-02T10:00:00',
      'status': 'pending',
      'total': 350,
      'commission_rate': 0.12,
      'commission': 42,
      'provider_net': 308,
      'payment_label': 'Simulated demo payment',
    });
    expect(booking.total, 350);
    expect(booking.commission, 42);
    expect(booking.providerNet, 308);
  });

  test('taxonomy category parses its service list', () {
    final category = TaxonomyCategory.fromJson({
      'key': 'vet',
      'label': 'Vets and veterinary clinics',
      'services': [
        {'key': 'vet_general', 'label': 'General and specialist checkup'},
      ],
    });
    expect(category.services.length, 1);
    expect(category.services.first.label, 'General and specialist checkup');
  });

  test('lost item parses kind and place', () {
    final item = LostItem.fromJson({
      'id': 1,
      'kind': 'lost',
      'title': 'Lost cat in Zamalek',
      'description': 'Grey cat, answers to Mimi',
      'pet_name': 'Mimi',
      'species': 'cat',
      'city': 'Cairo',
      'area': 'Zamalek',
      'status': 'open',
      'author_name': 'Sara',
    });
    expect(item.kind, 'lost');
    expect(item.city, 'Cairo');
  });
}
