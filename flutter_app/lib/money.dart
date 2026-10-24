// Money math that mirrors the backend exactly.
// The backend rounds commission to two decimals, then subtracts it from
// the total to get the provider net. Nothing here invents its own rule.
double roundMoney(double value) => (value * 100).round() / 100;

(double commission, double net) splitBooking(double total, double rate) {
  final commission = roundMoney(total * rate);
  return (commission, roundMoney(total - commission));
}

String egp(double value) => '${value.toStringAsFixed(2)} EGP';
