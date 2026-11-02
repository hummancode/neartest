import raw from "../../data/dis_ticaret.json";
export interface TradeItem { name: string; exports: number; imports?: number }
export interface Trade {
  source: string;
  partners?: { year: string; items: TradeItem[]; sample: boolean };
  products?: { year: string; items: TradeItem[]; sample: boolean };
}
export const trade = raw as unknown as Trade;
