-- GuardianEye PostgreSQL 16 + pgvector Initialization Script

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Create Schema Search Path
SET timezone = 'UTC';

-- 3. Core Roles Seed
INSERT INTO roles (id, name, description, permissions, created_at, updated_at)
VALUES 
  (gen_random_uuid()::text, 'Admin', 'System Administrator with full access', '*', NOW(), NOW()),
  (gen_random_uuid()::text, 'Supervisor', 'Warehouse Supervisor managing live alerts and reviews', 'read,write,review,ack', NOW(), NOW()),
  (gen_random_uuid()::text, 'Safety_Officer', 'Safety compliance and incident investigation officer', 'read,review,report,export', NOW(), NOW()),
  (gen_random_uuid()::text, 'Analyst', 'Operations and data analytics viewer', 'read,analytics,export', NOW(), NOW()),
  (gen_random_uuid()::text, 'Operator', 'Terminal display operator for live guidance', 'read,ack', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;
