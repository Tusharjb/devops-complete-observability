const express = require("express");
const client = require("prom-client");
const pino = require("pino");
const pinoHttp = require("pino-http");

const app = express();
const logger = pino();

app.use(pinoHttp({ logger }));

const register = new client.Registry();

client.collectDefaultMetrics({
  register,
  prefix: "cloudops_"
});

const httpRequests = new client.Counter({
  name: "cloudops_http_requests_total",
  help: "Total HTTP requests",
  labelNames: ["method", "route", "status_code"],
  registers: [register]
});

const httpDuration = new client.Histogram({
  name: "cloudops_http_request_duration_seconds",
  help: "HTTP request duration in seconds",
  labelNames: ["method", "route", "status_code"],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2],
  registers: [register]
});

app.use((req, res, next) => {
  if (req.path === "/metrics") return next();

  const end = httpDuration.startTimer();

  res.on("finish", () => {
    const labels = {
      method: req.method,
      route: req.route?.path || req.path,
      status_code: String(res.statusCode)
    };

    httpRequests.inc(labels);
    end(labels);
  });

  next();
});

app.get("/", (req, res) => {
  res.json({
    application: "CloudOps Observability",
    status: "running",
    version: "1.0.0",
    environment: process.env.NODE_ENV || "development",
    endpoints: ["/health", "/api/demo", "/metrics"]
  });
});

app.get("/health", (req, res) => {
  res.json({
    status: "UP",
    timestamp: new Date().toISOString()
  });
});

app.get("/api/demo", (req, res) => {
  req.log.info("Demo API request received");

  res.json({
    message: "Observability demo request successful",
    timestamp: new Date().toISOString()
  });
});

app.get("/api/error", (req, res) => {
  req.log.error("Simulated application error");

  res.status(500).json({
    error: "Simulated failure",
    note: "This endpoint is used for monitoring demonstrations"
  });
});

app.get("/metrics", async (req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});

const PORT = Number(process.env.PORT || 3000);

app.listen(PORT, "0.0.0.0", () => {
  logger.info({ port: PORT }, "CloudOps application started");
});