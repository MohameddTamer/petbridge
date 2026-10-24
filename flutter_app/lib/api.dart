// One small HTTP client for the PetBridge backend.
// The base URL is a single constant so the app can be pointed at any
// server without touching a screen. Auth is a bearer token from login,
// exactly like the web client sends it.
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models.dart';

const String defaultBaseUrl = 'http://127.0.0.1:8765';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

class ApiClient {
  final String baseUrl;
  String? token;
  ApiClient({this.baseUrl = defaultBaseUrl});

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Future<Map<String, dynamic>> _get(String path) async {
    final res = await http.get(Uri.parse('$baseUrl$path'), headers: _headers);
    return _decode(res);
  }

  Future<Map<String, dynamic>> _post(
      String path, Map<String, dynamic> body) async {
    final res = await http.post(Uri.parse('$baseUrl$path'),
        headers: _headers, body: jsonEncode(body));
    return _decode(res);
  }

  Map<String, dynamic> _decode(http.Response res) {
    if (res.body.isEmpty) {
      throw ApiException('Empty response from the server.');
    }
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    if (res.statusCode >= 400) {
      throw ApiException((body['error'] ?? 'Request failed').toString());
    }
    return body;
  }

  Future<void> login(String email, String password) async {
    final body = await _post('/api/auth/login', {
      'email': email,
      'password': password,
    });
    token = body['token'] as String?;
    if (token == null) throw ApiException('No session token returned');
  }

  Future<void> registerCustomer(
      String name, String email, String password) async {
    final body = await _post('/api/auth/register-customer', {
      'name': name,
      'email': email,
      'password': password,
    });
    token = body['token'] as String?;
  }

  Future<({List<Pet> pets, List<Map<String, dynamic>> due, List<Booking> bookings})>
      home() async {
    final body = await _get('/api/client/home');
    final pets = ((body['pets'] as List?) ?? [])
        .map((e) => Pet.fromJson(e as Map<String, dynamic>))
        .toList();
    final due = ((body['due'] as List?) ?? [])
        .map((e) => e as Map<String, dynamic>)
        .toList();
    final bookings = ((body['bookings'] as List?) ?? [])
        .map((e) => Booking.fromJson(e as Map<String, dynamic>))
        .toList();
    return (pets: pets, due: due, bookings: bookings);
  }

  Future<List<TaxonomyCategory>> taxonomy() async {
    final body = await _get('/api/taxonomy');
    return ((body['categories'] as List?) ?? [])
        .map((e) => TaxonomyCategory.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<ProviderEntry>> directory(
      {String category = '', String query = ''}) async {
    final params = <String, String>{};
    if (category.isNotEmpty) params['category'] = category;
    if (query.isNotEmpty) params['q'] = query;
    final qs = params.entries
        .map((e) =>
            '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}')
        .join('&');
    final body = await _get('/api/directory${qs.isEmpty ? '' : '?$qs'}');
    return ((body['providers'] as List?) ?? [])
        .map((e) => ProviderEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Booking> createBooking({
    required int serviceId,
    int? petId,
    int? slotId,
    String? startAt,
    String notes = '',
  }) async {
    final payload = <String, dynamic>{'service_id': serviceId, 'notes': notes};
    if (petId != null) payload['pet_id'] = petId;
    if (slotId != null) {
      payload['slot_id'] = slotId;
    } else if (startAt != null) {
      payload['start_at'] = startAt;
    }
    final body = await _post('/api/bookings', payload);
    return Booking.fromJson(body['booking'] as Map<String, dynamic>);
  }

  Future<Pet> addPet(Map<String, dynamic> fields) async {
    final body = await _post('/api/pets', fields);
    return Pet.fromJson(body['pet'] as Map<String, dynamic>);
  }

  Future<HealthRecord> addHealthRecord(
      int petId, Map<String, dynamic> fields) async {
    final body = await _post('/api/pets/$petId/health', fields);
    return HealthRecord.fromJson(body['record'] as Map<String, dynamic>);
  }

  Future<List<LostItem>> lostFound() async {
    final body = await _get('/api/lost-found');
    return ((body['items'] as List?) ?? [])
        .map((e) => LostItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<BreedResult> breedAnalyze({
    required String fileName,
    required String species,
    int? petId,
  }) async {
    final payload = <String, dynamic>{
      'file_name': fileName,
      'declared_species': species,
    };
    if (petId != null) payload['pet_id'] = petId;
    final body = await _post('/api/breed/analyze', payload);
    return BreedResult.fromJson(body);
  }
}
