// Plain data holders shaped exactly like the backend JSON.
// Every field name below comes from the backend dict helpers.

class HealthRecord {
  final int id;
  final String kind;
  final String name;
  final String givenDate;
  final String? nextDue;
  final String status;
  final String providerName;
  HealthRecord({
    required this.id,
    required this.kind,
    required this.name,
    required this.givenDate,
    required this.nextDue,
    required this.status,
    required this.providerName,
  });
  factory HealthRecord.fromJson(Map<String, dynamic> j) => HealthRecord(
        id: (j['id'] as num).toInt(),
        kind: (j['kind'] ?? 'checkup').toString(),
        name: (j['name'] ?? '').toString(),
        givenDate: (j['given_date'] ?? '').toString(),
        nextDue: j['next_due']?.toString(),
        status: (j['status'] ?? 'none').toString(),
        providerName: (j['provider_name'] ?? '').toString(),
      );
}

class Pet {
  final int id;
  final String name;
  final String species;
  final String breed;
  final String birthDate;
  final String ageLabel;
  final String sex;
  final double? weightKg;
  final String notes;
  final List<HealthRecord> healthRecords;
  Pet({
    required this.id,
    required this.name,
    required this.species,
    required this.breed,
    required this.birthDate,
    required this.ageLabel,
    required this.sex,
    required this.weightKg,
    required this.notes,
    required this.healthRecords,
  });
  factory Pet.fromJson(Map<String, dynamic> j) => Pet(
        id: (j['id'] as num).toInt(),
        name: (j['name'] ?? '').toString(),
        species: (j['species'] ?? '').toString(),
        breed: (j['breed'] ?? '').toString(),
        birthDate: (j['birth_date'] ?? '').toString(),
        ageLabel: (j['age_label'] ?? '').toString(),
        sex: (j['sex'] ?? '').toString(),
        weightKg: (j['weight_kg'] as num?)?.toDouble(),
        notes: (j['notes'] ?? '').toString(),
        healthRecords: ((j['health_records'] as List?) ?? [])
            .map((e) => HealthRecord.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
  List<HealthRecord> get dueItems => healthRecords
      .where((r) => r.status == 'overdue' || r.status == 'due_soon')
      .toList();
}

class Slot {
  final int id;
  final String date;
  final String startTime;
  final String endTime;
  final int remaining;
  Slot({
    required this.id,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.remaining,
  });
  factory Slot.fromJson(Map<String, dynamic> j) => Slot(
        id: (j['id'] as num).toInt(),
        date: (j['date'] ?? '').toString(),
        startTime: (j['start_time'] ?? '').toString(),
        endTime: (j['end_time'] ?? '').toString(),
        remaining: (j['remaining'] as num?)?.toInt() ?? 0,
      );
}

class DirectoryService {
  final int id;
  final int providerId;
  final String name;
  final String category;
  final String categoryLabel;
  final double price;
  final int durationMin;
  final String mode;
  final List<Slot> slots;
  DirectoryService({
    required this.id,
    required this.providerId,
    required this.name,
    required this.category,
    required this.categoryLabel,
    required this.price,
    required this.durationMin,
    required this.mode,
    required this.slots,
  });
  factory DirectoryService.fromJson(Map<String, dynamic> j) =>
      DirectoryService(
        id: (j['id'] as num).toInt(),
        providerId: (j['provider_id'] as num).toInt(),
        name: (j['name'] ?? '').toString(),
        category: (j['category'] ?? '').toString(),
        categoryLabel: (j['category_label'] ?? '').toString(),
        price: (j['price'] as num).toDouble(),
        durationMin: (j['duration_min'] as num?)?.toInt() ?? 0,
        mode: (j['mode'] ?? '').toString(),
        slots: ((j['slots'] as List?) ?? [])
            .map((e) => Slot.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class ProviderEntry {
  final int id;
  final String businessName;
  final String city;
  final String area;
  final double? rating;
  final int reviewsCount;
  final List<DirectoryService> services;
  ProviderEntry({
    required this.id,
    required this.businessName,
    required this.city,
    required this.area,
    required this.rating,
    required this.reviewsCount,
    required this.services,
  });
  factory ProviderEntry.fromJson(Map<String, dynamic> j) => ProviderEntry(
        id: (j['id'] as num).toInt(),
        businessName: (j['business_name'] ?? '').toString(),
        city: (j['city'] ?? '').toString(),
        area: (j['area'] ?? '').toString(),
        rating: (j['rating'] as num?)?.toDouble(),
        reviewsCount: (j['reviews_count'] as num?)?.toInt() ?? 0,
        services: ((j['services'] as List?) ?? [])
            .map((e) => DirectoryService.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class TaxonomyService {
  final String key;
  final String label;
  TaxonomyService({required this.key, required this.label});
  factory TaxonomyService.fromJson(Map<String, dynamic> j) =>
      TaxonomyService(
        key: (j['key'] ?? '').toString(),
        label: (j['label'] ?? '').toString(),
      );
}

class TaxonomyCategory {
  final String key;
  final String label;
  final List<TaxonomyService> services;
  TaxonomyCategory({
    required this.key,
    required this.label,
    required this.services,
  });
  factory TaxonomyCategory.fromJson(Map<String, dynamic> j) =>
      TaxonomyCategory(
        key: (j['key'] ?? '').toString(),
        label: (j['label'] ?? '').toString(),
        services: ((j['services'] as List?) ?? [])
            .map((e) => TaxonomyService.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class Booking {
  final int id;
  final String businessName;
  final String serviceName;
  final String? petName;
  final String startAt;
  final String status;
  final double total;
  final double commissionRate;
  final double commission;
  final double providerNet;
  final String paymentLabel;
  Booking({
    required this.id,
    required this.businessName,
    required this.serviceName,
    required this.petName,
    required this.startAt,
    required this.status,
    required this.total,
    required this.commissionRate,
    required this.commission,
    required this.providerNet,
    required this.paymentLabel,
  });
  factory Booking.fromJson(Map<String, dynamic> j) => Booking(
        id: (j['id'] as num).toInt(),
        businessName: (j['business_name'] ?? '').toString(),
        serviceName: (j['service_name'] ?? '').toString(),
        petName: j['pet_name']?.toString(),
        startAt: (j['start_at'] ?? '').toString(),
        status: (j['status'] ?? '').toString(),
        total: (j['total'] as num).toDouble(),
        commissionRate: (j['commission_rate'] as num).toDouble(),
        commission: (j['commission'] as num).toDouble(),
        providerNet: (j['provider_net'] as num).toDouble(),
        paymentLabel: (j['payment_label'] ?? '').toString(),
      );
}

class LostItem {
  final int id;
  final String kind;
  final String title;
  final String description;
  final String petName;
  final String species;
  final String city;
  final String area;
  final String status;
  final String authorName;
  LostItem({
    required this.id,
    required this.kind,
    required this.title,
    required this.description,
    required this.petName,
    required this.species,
    required this.city,
    required this.area,
    required this.status,
    required this.authorName,
  });
  factory LostItem.fromJson(Map<String, dynamic> j) => LostItem(
        id: (j['id'] as num).toInt(),
        kind: (j['kind'] ?? '').toString(),
        title: (j['title'] ?? '').toString(),
        description: (j['description'] ?? '').toString(),
        petName: (j['pet_name'] ?? '').toString(),
        species: (j['species'] ?? '').toString(),
        city: (j['city'] ?? '').toString(),
        area: (j['area'] ?? '').toString(),
        status: (j['status'] ?? '').toString(),
        authorName: (j['author_name'] ?? '').toString(),
      );
}

class BreedResult {
  final bool beta;
  final String label;
  final String species;
  final String breed;
  final String summary;
  final String care;
  final String note;
  BreedResult({
    required this.beta,
    required this.label,
    required this.species,
    required this.breed,
    required this.summary,
    required this.care,
    required this.note,
  });
  factory BreedResult.fromJson(Map<String, dynamic> j) => BreedResult(
        beta: j['beta'] == true,
        label: (j['label'] ?? '').toString(),
        species: (j['species'] ?? '').toString(),
        breed: (j['breed'] ?? '').toString(),
        summary: (j['summary'] ?? '').toString(),
        care: (j['care'] ?? '').toString(),
        note: (j['note'] ?? '').toString(),
      );
}
