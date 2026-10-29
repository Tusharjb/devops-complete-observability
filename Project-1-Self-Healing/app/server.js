const express = require("express");
const client = require("prom-client");

const app = express();
const PORT = process.env.PORT || 3000;

let healthy = true;

// Prometheus registry
const register = new client.Registry();

client.collectDefaultMetrics({
  register,
  prefix: "selfhealing_"
});

// Custom application health metric
const healthGauge = new client.Gauge({
  name: "selfhealing_app_healthy",
  help: "Application health status: 1 = healthy, 0 = unhealthy",
  registers: [register]
});

healthGauge.set(1);

// HTTP request counter
const requestCounter = new client.Counter({
  name: "selfhealing_http_requests_total",
  help: "Total HTTP requests",
  labelNames: ["method", "route", "status_code"],
  registers: [register]
});

// Request tracking
app.use((req, res, next) => {
  res.on("finish", () => {
    requestCounter.inc({
      method: req.method,
      route: req.route?.path || req.path,
      status_code: String(res.statusCode)
    });
  });

  next();
});

// Home
app.get("/", (req, res) => {
  res.json({
    application: "CloudOps Self-Healing Demo",
    status: healthy ? "HEALTHY" : "UNHEALTHY"
  });
});

// Health endpoint
app.get("/health", (req, res) => {
  if (!healthy) {
    return res.status(503).json({
      status: "DOWN",
      message: "Simulated application failure"
    });
  }

  res.json({ status: "UP" });
});

// Normal request
app.get("/api/demo", (req, res) => {
  res.json({
    success: true,
    message: "Self-healing application is running"
  });
});

// Simulate failure
app.post("/admin/fail", (req, res) => {
  healthy = false;
  healthGauge.set(0);

  console.log("SIMULATED FAILURE: Application unhealthy");

  res.json({
    success: true,
    status: "UNHEALTHY"
  });
});

// Manual recovery
app.post("/admin/recover", (req, res) => {
  healthy = true;
  healthGauge.set(1);

  console.log("MANUAL RECOVERY: Application healthy");

  res.json({
    success: true,
    status: "HEALTHY"
  });
});

// Prometheus metrics
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Self-healing application listening on port ${PORT}`);
});