// Commission math must match the backend, case for case.
import 'package:flutter_test/flutter_test.dart';
import 'package:petbridge_client/money.dart';

void main() {
  test('the verified booking splits 350 into 42 and 308', () {
    final (commission, net) = splitBooking(350, 0.12);
    expect(commission, 42);
    expect(net, 308);
  });

  test('the seed completed booking splits 500 into 60 and 440', () {
    final (commission, net) = splitBooking(500, 0.12);
    expect(commission, 60);
    expect(net, 440);
  });

  test('the shop order rate of 10 percent splits 170 into 17 and 153', () {
    final (commission, net) = splitBooking(170, 0.10);
    expect(commission, 17);
    expect(net, 153);
  });

  test('rounding stays at two decimals', () {
    expect(roundMoney(10.005), 10.01);
    expect(roundMoney(42.0), 42);
  });

  test('money prints with two decimals and EGP', () {
    expect(egp(42), '42.00 EGP');
    expect(egp(308.5), '308.50 EGP');
  });
}
