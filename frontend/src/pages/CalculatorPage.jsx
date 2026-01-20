/**
 * Calculator Page - Yatırım Hesaplayıcı
 * Pozisyon boyutu, kar/zarar, risk hesaplamaları
 */
import React, { useState, useEffect } from "react";
import {
  Calculator,
  DollarSign,
  Percent,
  Target,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  PieChart,
  Scale,
  Wallet,
  BarChart3,
} from "lucide-react";

const CalculatorPage = () => {
  // Position Size Calculator
  const [capital, setCapital] = useState(100000);
  const [riskPercent, setRiskPercent] = useState(2);
  const [entryPrice, setEntryPrice] = useState(100);
  const [stopLoss, setStopLoss] = useState(95);

  // Profit Calculator
  const [buyPrice, setBuyPrice] = useState(100);
  const [sellPrice, setSellPrice] = useState(120);
  const [quantity, setQuantity] = useState(100);
  const [commission, setCommission] = useState(0.1);

  // Compound Interest Calculator
  const [principal, setPrincipal] = useState(10000);
  const [monthlyReturn, setMonthlyReturn] = useState(5);
  const [months, setMonths] = useState(12);

  // Position Size Calculations
  const riskAmount = capital * (riskPercent / 100);
  const stopLossPercent = ((entryPrice - stopLoss) / entryPrice) * 100;
  const positionSize =
    stopLossPercent > 0 ? riskAmount / (stopLossPercent / 100) : 0;
  const shareCount = positionSize / entryPrice;
  const maxLoss = shareCount * (entryPrice - stopLoss);

  // Profit Calculations
  const totalBuyCost = buyPrice * quantity * (1 + commission / 100);
  const totalSellRevenue = sellPrice * quantity * (1 - commission / 100);
  const grossProfit = (sellPrice - buyPrice) * quantity;
  const netProfit = totalSellRevenue - totalBuyCost;
  const profitPercent = ((sellPrice - buyPrice) / buyPrice) * 100;
  const commissionCost =
    (buyPrice * quantity * commission) / 100 +
    (sellPrice * quantity * commission) / 100;

  // Compound Interest Calculations
  const compoundResults = [];
  let currentAmount = principal;
  for (let i = 1; i <= months; i++) {
    currentAmount = currentAmount * (1 + monthlyReturn / 100);
    compoundResults.push({
      month: i,
      amount: currentAmount,
      profit: currentAmount - principal,
    });
  }
  const finalAmount =
    compoundResults.length > 0
      ? compoundResults[compoundResults.length - 1].amount
      : principal;
  const totalProfit = finalAmount - principal;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("tr-TR", {
      style: "currency",
      currency: "TRY",
      minimumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div className="space-y-3 sm:space-y-4 md:space-y-6">
      {/* Calculator Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 md:gap-6">
        {/* Position Size Calculator */}
        <div className="card">
          <div className="p-2 sm:p-3 md:p-4 border-b border-[var(--color-border)]">
            <div className="flex items-center gap-1.5 sm:gap-2 md:gap-3">
              <div className="w-7 h-7 sm:w-8 sm:h-8 md:w-10 md:h-10 rounded-lg sm:rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Scale className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5 text-primary" />
              </div>
              <div className="min-w-0">
                <h2 className="font-semibold text-xs sm:text-sm md:text-base text-theme-text truncate">
                  Pozisyon Boyutu
                </h2>
                <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted hidden sm:block">
                  Risk bazlı lot hesaplama
                </p>
              </div>
            </div>
          </div>

          <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:gap-3 md:gap-4">
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Sermaye (₺)
                </label>
                <input
                  type="number"
                  value={capital}
                  onChange={(e) => setCapital(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Risk (%)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={riskPercent}
                  onChange={(e) => setRiskPercent(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Giriş Fiyatı (₺)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Stop Loss (₺)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={stopLoss}
                  onChange={(e) => setStopLoss(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
            </div>

            <div className="bg-[var(--color-bg-tertiary)] rounded-xl p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-theme-muted">Risk Tutarı</span>
                <span className="font-semibold text-theme-text">
                  {formatCurrency(riskAmount)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Stop Loss Mesafesi</span>
                <span className="font-semibold text-red-500">
                  %{stopLossPercent.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Pozisyon Boyutu</span>
                <span className="font-semibold text-primary">
                  {formatCurrency(positionSize)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Alınacak Lot</span>
                <span className="font-bold text-lg text-theme-text">
                  {Math.floor(shareCount)} lot
                </span>
              </div>
              <div className="flex justify-between border-t border-[var(--color-border)] pt-3">
                <span className="text-theme-muted">Maksimum Zarar</span>
                <span className="font-semibold text-red-500">
                  {formatCurrency(maxLoss)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Profit/Loss Calculator */}
        <div className="card">
          <div className="p-2 sm:p-3 md:p-4 border-b border-[var(--color-border)]">
            <div className="flex items-center gap-1.5 sm:gap-2 md:gap-3">
              <div className="w-7 h-7 sm:w-8 sm:h-8 md:w-10 md:h-10 rounded-lg sm:rounded-xl bg-green-500/10 flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5 text-green-500" />
              </div>
              <div className="min-w-0">
                <h2 className="font-semibold text-xs sm:text-sm md:text-base text-theme-text truncate">
                  Kar/Zarar Hesaplama
                </h2>
                <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted hidden sm:block">
                  İşlem kar/zarar analizi
                </p>
              </div>
            </div>
          </div>

          <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
            <div className="grid grid-cols-2 gap-2 sm:gap-3 md:gap-4">
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Alış Fiyatı (₺)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={buyPrice}
                  onChange={(e) => setBuyPrice(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Satış Fiyatı (₺)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={sellPrice}
                  onChange={(e) => setSellPrice(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Miktar (Lot)
                </label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
              <div>
                <label className="block text-[10px] sm:text-xs md:text-sm text-theme-muted mb-1">
                  Komisyon (%)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={commission}
                  onChange={(e) => setCommission(Number(e.target.value))}
                  className="input-field w-full text-sm"
                />
              </div>
            </div>

            <div className="bg-[var(--color-bg-tertiary)] rounded-xl p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-theme-muted">Toplam Alış Maliyeti</span>
                <span className="font-semibold text-theme-text">
                  {formatCurrency(totalBuyCost)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Toplam Satış Geliri</span>
                <span className="font-semibold text-theme-text">
                  {formatCurrency(totalSellRevenue)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Komisyon Maliyeti</span>
                <span className="font-semibold text-orange-500">
                  {formatCurrency(commissionCost)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-theme-muted">Brüt Kar/Zarar</span>
                <span
                  className={`font-semibold ${
                    grossProfit >= 0 ? "text-green-500" : "text-red-500"
                  }`}
                >
                  {formatCurrency(grossProfit)}
                </span>
              </div>
              <div className="flex justify-between border-t border-[var(--color-border)] pt-3">
                <span className="text-theme-muted">Net Kar/Zarar</span>
                <span
                  className={`font-bold text-lg ${
                    netProfit >= 0 ? "text-green-500" : "text-red-500"
                  }`}
                >
                  {formatCurrency(netProfit)} ({profitPercent >= 0 ? "+" : ""}
                  {profitPercent.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Compound Interest Calculator */}
      <div className="card">
        <div className="p-4 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <h2 className="font-semibold text-theme-text">
                Bileşik Getiri Hesaplama
              </h2>
              <p className="text-xs text-theme-muted">
                Aylık düzenli getiri projeksiyonu
              </p>
            </div>
          </div>
        </div>

        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm text-theme-muted mb-1">
                Başlangıç Sermayesi (₺)
              </label>
              <input
                type="number"
                value={principal}
                onChange={(e) => setPrincipal(Number(e.target.value))}
                className="input-field w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-theme-muted mb-1">
                Aylık Getiri (%)
              </label>
              <input
                type="number"
                step="0.5"
                value={monthlyReturn}
                onChange={(e) => setMonthlyReturn(Number(e.target.value))}
                className="input-field w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-theme-muted mb-1">
                Süre (Ay)
              </label>
              <input
                type="number"
                value={months}
                onChange={(e) =>
                  setMonths(Math.min(Number(e.target.value), 60))
                }
                className="input-field w-full"
              />
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-[var(--color-bg-tertiary)] rounded-xl p-4 text-center">
              <Wallet className="w-6 h-6 text-theme-muted mx-auto mb-2" />
              <p className="text-xs text-theme-muted">Başlangıç</p>
              <p className="font-bold text-theme-text">
                {formatCurrency(principal)}
              </p>
            </div>
            <div className="bg-[var(--color-bg-tertiary)] rounded-xl p-4 text-center">
              <Target className="w-6 h-6 text-purple-500 mx-auto mb-2" />
              <p className="text-xs text-theme-muted">Final Değer</p>
              <p className="font-bold text-purple-500">
                {formatCurrency(finalAmount)}
              </p>
            </div>
            <div className="bg-[var(--color-bg-tertiary)] rounded-xl p-4 text-center">
              <TrendingUp className="w-6 h-6 text-green-500 mx-auto mb-2" />
              <p className="text-xs text-theme-muted">Toplam Kar</p>
              <p className="font-bold text-green-500">
                {formatCurrency(totalProfit)}
              </p>
            </div>
            <div className="bg-[var(--color-bg-tertiary)] rounded-xl p-4 text-center">
              <Percent className="w-6 h-6 text-primary mx-auto mb-2" />
              <p className="text-xs text-theme-muted">Toplam Getiri</p>
              <p className="font-bold text-primary">
                {((totalProfit / principal) * 100).toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Monthly Progress */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[var(--color-bg-tertiary)]">
                <tr>
                  <th className="px-4 py-2 text-left text-theme-muted">Ay</th>
                  <th className="px-4 py-2 text-right text-theme-muted">
                    Bakiye
                  </th>
                  <th className="px-4 py-2 text-right text-theme-muted">
                    Aylık Kar
                  </th>
                  <th className="px-4 py-2 text-right text-theme-muted">
                    Toplam Kar
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {compoundResults.slice(0, 12).map((row, idx) => {
                  const prevAmount =
                    idx === 0 ? principal : compoundResults[idx - 1].amount;
                  const monthlyProfit = row.amount - prevAmount;
                  return (
                    <tr
                      key={row.month}
                      className="hover:bg-[var(--color-bg-secondary)]"
                    >
                      <td className="px-4 py-2 font-medium text-theme-text">
                        {row.month}. Ay
                      </td>
                      <td className="px-4 py-2 text-right text-theme-text">
                        {formatCurrency(row.amount)}
                      </td>
                      <td className="px-4 py-2 text-right text-green-500">
                        +{formatCurrency(monthlyProfit)}
                      </td>
                      <td className="px-4 py-2 text-right text-primary">
                        +{formatCurrency(row.profit)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {compoundResults.length > 12 && (
              <div className="text-center py-3 text-sm text-theme-muted">
                ... ve {compoundResults.length - 12} ay daha
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Tips */}
      <div className="card p-4">
        <h3 className="font-semibold text-theme-text mb-3">
          💡 Hesaplama İpuçları
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <p className="text-theme-muted">
              <strong className="text-theme-text">Risk Yönetimi:</strong> Tek
              işlemde sermayenizin %1-2'sinden fazlasını riske atmayın.
            </p>
          </div>
          <div className="flex items-start gap-2">
            <Target className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <p className="text-theme-muted">
              <strong className="text-theme-text">Risk/Ödül:</strong> En az 1:2
              risk/ödül oranı hedefleyin.
            </p>
          </div>
          <div className="flex items-start gap-2">
            <Scale className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <p className="text-theme-muted">
              <strong className="text-theme-text">Pozisyon:</strong> Hesaplanan
              lot sayısını asla aşmayın.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalculatorPage;
