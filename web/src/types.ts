export type Language = "en" | "bn";

export interface DetectionBox {
  box: [number, number, number, number];
  food_class: string;
  name_en: string;
  name_bn: string;
  confidence: number;
  estimated_grams: number;
  cost_value_bdt: number;
  sales_value_bdt: number;
  area_cm2: number;
  waste_category: string;
}

export interface ScanResult {
  success: boolean;
  boxes: DetectionBox[];
  plate_state: "empty_plate" | "partial_leftover" | "full_plate";
  coverage_ratio: number;
  total_leftover_grams: number;
  total_cost_bdt: number;
  total_sales_bdt: number;
  inference_time_ms: number;
  is_mock: boolean;
  mock_reason?: string;
  image_base64?: string;
  frame_filename?: string;
  image_dims?: { width: number; height: number };
}

export interface ModelStatus {
  is_mock: boolean;
  mock_reason: string;
  model_path: string;
  model_exists: boolean;
  classes_count: number;
  classes: string[];
  food_classes: string[];
  target_latency_ms: string;
  calibration_loaded: boolean;
  timestamp: string;
}

export interface DailyForecastItem {
  id: number;
  forecast_date: string;
  meal_period: string;
  food_class: string;
  forecast_portions: number;
  lower_bound: number;
  upper_bound: number;
  actual_consumed?: number;
  day_of_week?: string;
  weather_flag: string;
  event_flag: string;
}

export interface OrderItem {
  id: number;
  date: string;
  meal_period: string;
  food_class: string;
  recommended_portions: number;
  safety_stock: number;
  current_stock: number;
  lead_time_hours: number;
  status: "pending" | "accepted" | "overridden";
  override_reason?: string;
}

export interface DiscountOfferItem {
  id: number;
  inventory_item_id?: number;
  food_class: string;
  discount_tier: number;
  discount_percent: number;
  original_price_bdt: number;
  discounted_price_bdt: number;
  reason: string;
  active_until: string;
  is_active: boolean;
}

export interface WasteBinItem {
  id: number;
  category: "edible_surplus" | "animal_feed" | "compost" | "general";
  name_en: string;
  name_bn: string;
  capacity_kg: number;
  current_weight_kg: number;
  fill_percentage: number;
  destination: string;
  status: "normal" | "nearing_capacity" | "pickup_scheduled";
}

export interface ManifestItem {
  id: number;
  manifest_code: string;
  timestamp: string;
  category: string;
  total_kg: number;
  destination: string;
  status: string;
  notes?: string;
}

export interface AgentLogItem {
  id: number;
  timestamp: string;
  agent_name: string;
  action: string;
  rationale: string;
  metadata_json?: string;
}

export interface SimulationResult {
  num_runs: number;
  days_per_run: number;
  headline_reduction_pct: number;
  std_reduction_pct: number;
  mean_waste_saved_kg: number;
  mean_cost_saved_bdt: number;
  target_achieved: boolean;
  confidence_interval_95: [number, number];
  representative_run: {
    seed: number;
    days: number;
    baseline: {
      waste_kg: number;
      waste_bdt: number;
      revenue_bdt: number;
      service_level_pct: number;
    };
    wastewise_ai: {
      waste_kg: number;
      waste_bdt: number;
      revenue_bdt: number;
      service_level_pct: number;
    };
    impact: {
      waste_reduction_pct: number;
      waste_saved_kg: number;
      cost_saved_bdt: number;
      revenue_gain_bdt: number;
    };
    daily_timeline: Array<{
      day: number;
      baseline_waste_kg: number;
      wastewise_waste_kg: number;
      waste_saved_kg: number;
    }>;
  };
}

