// ============ ALL MOCK DATA IN ONE FILE ============
// When USE_MOCK = true in api.ts, these responses are used instead of real API calls.
// When backend is ready, set USE_MOCK = false and delete this file.

export const mockData = {

  // POST /context response
  contextResponse: {
    experiment_id: 1,
    context_id: 1,
    hypothesis: {
      experiment_name: "Checkout Simplification",
      hypothesis: "Reducing checkout friction improves conversion for returning shoppers",
      primary_metric: "checkout_conversion",
      secondary_metrics: ["average_order_value"],
      guardrail_metrics: ["bounce_rate", "error_rate"]
    },
    configuration: {
      feature_flag: "checkout_v2",
      audience: "returning_users",
      traffic_split_option: "50_50",
      traffic_split: { control: 0.5, variant: 0.5 },
      duration_days: 14,
      sample_size: 5000,
      confidence_level: 0.95,
      baseline_conversion_rate: 0.041,
      expected_lift: 0.15
    },
    status: "draft"
  },

  // POST /validate response
  validateResponse: {
    decision: "approve",
    explanation: "All validation rules passed. Experiment is ready to launch.",
    validation_score: 0.92,
    warnings: [] as string[],
    suggestions: [] as string[],
    rules_matched: [
      { rule_id: "traffic_split_sums_to_one", name: "Traffic split must sum to 1.0", matched: true, decision: "approve", message: "Traffic split sums to 1.0." },
      { rule_id: "traffic_control_positive", name: "Control arm must receive traffic", matched: true, decision: "approve", message: "Control arm allocated." },
      { rule_id: "traffic_variant_positive", name: "Variant arm must receive traffic", matched: true, decision: "approve", message: "Variant arm allocated." },
      { rule_id: "audience_specified", name: "Target audience must be specified", matched: true, decision: "approve", message: "Audience specified." },
      { rule_id: "primary_metric_defined", name: "A primary success metric must be defined", matched: true, decision: "approve", message: "Primary metric defined." },
      { rule_id: "duration_reasonable", name: "Experiment duration must be between 1 and 90 days", matched: true, decision: "approve", message: "Duration is within accepted bounds." },
      { rule_id: "min_sample_size", name: "Sample size must be at least 1000 users per arm", matched: true, decision: "approve", message: "Sample size is sufficient." },
      { rule_id: "feature_flag_naming", name: "Feature flag name follows snake_case convention", matched: true, decision: "approve", message: "Feature flag name is valid." },
      { rule_id: "confidence_level_valid", name: "Confidence level should be at least 0.90", matched: true, decision: "approve", message: "Confidence level is acceptable." },
      { rule_id: "guardrail_metrics_present", name: "At least one guardrail metric should be defined", matched: true, decision: "approve", message: "Guardrail metric(s) defined." }
    ],
    rules_rejected: [] as any[]
  },

  // GET /experiment/:id/metrics response
  metricsResponse: {
    experiment_id: 1,
    latest: {
      id: 214,
      experiment_id: 1,
      users_control: 12484,
      users_variant: 12516,
      conversion_control: 547,
      conversion_variant: 626,
      revenue_control: 22190.35,
      revenue_variant: 25876.90,
      confidence: 0.9796,
      p_value: 0.0204,
      conversion_lift: 0.1411,
      timestamp: "2026-07-24T18:11:05Z"
    },
    series: [
      { id: 1, users_control: 2500, users_variant: 2510, conversion_control: 105, conversion_variant: 125, revenue_control: 4200, revenue_variant: 5100, confidence: 0.62, p_value: 0.38, conversion_lift: 0.08, timestamp: "2026-07-24T18:00:05Z" },
      { id: 2, users_control: 4800, users_variant: 4850, conversion_control: 205, conversion_variant: 248, revenue_control: 8400, revenue_variant: 10200, confidence: 0.72, p_value: 0.28, conversion_lift: 0.10, timestamp: "2026-07-24T18:02:05Z" },
      { id: 3, users_control: 6900, users_variant: 6950, conversion_control: 298, conversion_variant: 355, revenue_control: 12100, revenue_variant: 14600, confidence: 0.81, p_value: 0.19, conversion_lift: 0.11, timestamp: "2026-07-24T18:04:05Z" },
      { id: 4, users_control: 8600, users_variant: 8680, conversion_control: 372, conversion_variant: 438, revenue_control: 15200, revenue_variant: 18100, confidence: 0.88, p_value: 0.12, conversion_lift: 0.12, timestamp: "2026-07-24T18:06:05Z" },
      { id: 5, users_control: 9800, users_variant: 9825, conversion_control: 421, conversion_variant: 502, revenue_control: 17420, revenue_variant: 20800, confidence: 0.92, p_value: 0.08, conversion_lift: 0.13, timestamp: "2026-07-24T18:08:05Z" },
      { id: 6, users_control: 11200, users_variant: 11300, conversion_control: 488, conversion_variant: 572, revenue_control: 19800, revenue_variant: 23500, confidence: 0.95, p_value: 0.05, conversion_lift: 0.13, timestamp: "2026-07-24T18:10:05Z" },
      { id: 7, users_control: 12484, users_variant: 12516, conversion_control: 547, conversion_variant: 626, revenue_control: 22190, revenue_variant: 25877, confidence: 0.9796, p_value: 0.0204, conversion_lift: 0.1411, timestamp: "2026-07-24T18:11:05Z" }
    ],
    statistics: {
      p_value: 0.0204,
      confidence: 0.9796,
      conversion_lift: 0.1411,
      z_score: 2.318,
      control_conversion_rate: 0.0438,
      variant_conversion_rate: 0.0500,
      winner: "variant",
      is_significant: true
    },
    recommendation: {
      recommendation: "scale",
      rationale: "Variant B increased checkout conversion by 14%, driven by a simpler payment flow, with no guardrail regressions observed.",
      confidence: 0.9796
    }
  },

  // POST /report/:id response
  reportResponse: {
    id: 1,
    experiment_id: 1,
    summary: "The Checkout Simplification experiment ran for 14 days against a 50/50 split of returning customers. Variant B, a simplified checkout flow, delivered a statistically significant 14.1% lift in checkout conversion (95%+ confidence) with no guardrail regressions in bounce rate or error rate.",
    recommendation: "scale",
    business_impact: "+14.1% conversion lift",
    next_steps: [
      "Rollout to 100%",
      "Continue monitoring performance",
      "Keep guardrail metrics active"
    ],
    details: {
      business_goal: "Increase checkout conversion by 15% among returning customers",
      hypothesis: {
        experiment_name: "Checkout Simplification",
        hypothesis: "Reducing checkout friction improves conversion for returning shoppers",
        primary_metric: "checkout_conversion"
      },
      configuration: {
        feature_flag: "checkout_v2",
        audience: "returning_users",
        traffic_split: { control: 0.5, variant: 0.5 }
      },
      statistics: {
        confidence: 0.9796,
        conversion_lift: 0.1411,
        winner: "variant"
      }
    },
    generated_at: "2026-07-24T18:15:00Z"
  }
}
