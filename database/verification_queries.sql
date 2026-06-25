-- Verification Queries for Task 3.2 Migration
-- Run these queries to verify the migration was applied correctly

-- ============================================================================
-- 1. VERIFY TABLES EXIST
-- ============================================================================

-- Check if allocations table exists and has correct columns
SELECT 
  table_name, 
  column_name, 
  data_type, 
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'allocations'
ORDER BY ordinal_position;

-- Check if audit_logs table exists and has correct columns
SELECT 
  table_name, 
  column_name, 
  data_type, 
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_name = 'audit_logs'
ORDER BY ordinal_position;

-- ============================================================================
-- 2. VERIFY FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- List all foreign keys for allocations table
SELECT 
  constraint_name,
  table_name,
  column_name,
  referenced_table_name,
  referenced_column_name
FROM information_schema.referential_constraints
JOIN information_schema.key_column_usage 
  ON information_schema.referential_constraints.constraint_name = information_schema.key_column_usage.constraint_name
WHERE table_name IN ('allocations', 'audit_logs')
ORDER BY constraint_name;

-- Alternative PostgreSQL query for foreign keys
SELECT 
  tc.constraint_name,
  tc.table_name,
  kcu.column_name,
  ccu.table_name AS foreign_table_name,
  ccu.column_name AS foreign_column_name,
  rc.update_rule,
  rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
  ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('allocations', 'audit_logs')
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- 3. VERIFY INDEXES EXIST
-- ============================================================================

-- List all indexes for allocations table
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'allocations'
ORDER BY indexname;

-- List all indexes for audit_logs table
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'audit_logs'
ORDER BY indexname;

-- Summary of all indexes created by this migration
SELECT 
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND (tablename IN ('allocations', 'audit_logs') 
       OR indexname LIKE 'idx_%')
ORDER BY tablename, indexname;

-- ============================================================================
-- 4. VERIFY CHECK CONSTRAINTS
-- ============================================================================

-- List check constraints for allocations and audit_logs
SELECT 
  constraint_name,
  table_name,
  column_name,
  data_type
FROM information_schema.constraint_column_usage
WHERE table_name IN ('allocations', 'audit_logs')
AND constraint_type = 'CHECK';

-- PostgreSQL-specific check constraints
SELECT 
  n.nspname,
  t.relname,
  c.conname,
  pg_get_constraintdef(c.oid)
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
JOIN pg_namespace n ON t.relnamespace = n.oid
WHERE t.relname IN ('allocations', 'audit_logs')
  AND c.contype = 'c'
ORDER BY t.relname, c.conname;

-- ============================================================================
-- 5. VERIFY DEFAULT VALUES
-- ============================================================================

-- Check default values for allocations table
SELECT 
  column_name,
  column_default,
  data_type
FROM information_schema.columns
WHERE table_name = 'allocations'
  AND column_default IS NOT NULL;

-- Check default values for audit_logs table
SELECT 
  column_name,
  column_default,
  data_type
FROM information_schema.columns
WHERE table_name = 'audit_logs'
  AND column_default IS NOT NULL;

-- ============================================================================
-- 6. TEST REFERENTIAL INTEGRITY (Non-Destructive)
-- ============================================================================

-- Count records in each table
SELECT 
  'allocations' as table_name,
  COUNT(*) as record_count
FROM allocations
UNION ALL
SELECT 
  'audit_logs' as table_name,
  COUNT(*) as record_count
FROM audit_logs;

-- Verify no orphaned allocations exist (should be 0 if starting fresh)
SELECT COUNT(*) as orphaned_allocations
FROM allocations a
WHERE NOT EXISTS (SELECT 1 FROM resources r WHERE r.id = a.resource_id)
   OR NOT EXISTS (SELECT 1 FROM projects p WHERE p.id = a.project_id)
   OR NOT EXISTS (SELECT 1 FROM users u WHERE u.id = a.created_by);

-- Verify no orphaned audit_logs exist (should be 0 if starting fresh)
SELECT COUNT(*) as orphaned_audit_logs
FROM audit_logs al
WHERE al.user_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = al.user_id);

-- ============================================================================
-- 7. PERFORMANCE VERIFICATION
-- ============================================================================

-- Analyze table to update statistics
ANALYZE allocations;
ANALYZE audit_logs;

-- Check index size and usage
SELECT 
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename IN ('allocations', 'audit_logs')
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('allocations', 'audit_logs')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- 8. QUERY PERFORMANCE TEST (Optional - creates test data)
-- ============================================================================

-- This section is commented out to prevent accidental data creation
-- Uncomment to test performance with sample data

/*
-- Create sample test data
INSERT INTO allocations (resource_id, project_id, cost_at_allocation, created_by)
SELECT 
  r.id,
  r.project_id,
  r.cost,
  r.created_by
FROM resources r
LIMIT 100;

-- Test allocation lookup by project (should use index)
EXPLAIN ANALYZE
SELECT 
  a.id,
  a.allocated_at,
  a.cost_at_allocation,
  r.id as resource_id
FROM allocations a
JOIN resources r ON a.resource_id = r.id
WHERE a.project_id = (SELECT id FROM projects LIMIT 1)
ORDER BY a.allocated_at DESC;

-- Test audit log lookup by entity (should use composite index)
EXPLAIN ANALYZE
SELECT 
  al.id,
  al.operation,
  al.created_at,
  al.status
FROM audit_logs al
WHERE al.entity_type = 'Resource'
  AND al.operation IN ('CREATE', 'UPDATE')
  AND al.created_at >= NOW() - INTERVAL '30 days'
ORDER BY al.created_at DESC;

-- Test budget calculation query (should use allocations indexes)
EXPLAIN ANALYZE
SELECT 
  p.id,
  p.name,
  p.budget,
  COALESCE(SUM(a.cost_at_allocation), 0) as allocated_amount
FROM projects p
LEFT JOIN allocations a ON p.id = a.project_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name, p.budget;
*/

-- ============================================================================
-- 9. CONSTRAINT VALIDATION SUMMARY
-- ============================================================================

-- Summary report of all constraints and indexes
SELECT 
  'Foreign Keys' as constraint_type,
  COUNT(*) as count
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
  AND table_name IN ('allocations', 'audit_logs')
UNION ALL
SELECT 
  'Check Constraints' as constraint_type,
  COUNT(*) as count
FROM pg_constraint c
JOIN pg_class t ON c.conrelid = t.oid
WHERE c.contype = 'c'
  AND t.relname IN ('allocations', 'audit_logs')
UNION ALL
SELECT 
  'Indexes' as constraint_type,
  COUNT(*) as count
FROM pg_indexes
WHERE tablename IN ('allocations', 'audit_logs');

-- ============================================================================
-- 10. DATA TYPE VALIDATION
-- ============================================================================

-- Verify JSONB columns in audit_logs can store JSON
-- (non-destructive test - just checks column types)
SELECT 
  column_name,
  data_type,
  udt_name
FROM information_schema.columns
WHERE table_name = 'audit_logs'
  AND data_type = 'jsonb';

-- Verify UUID columns are properly typed
SELECT 
  table_name,
  column_name,
  data_type,
  udt_name
FROM information_schema.columns
WHERE (table_name IN ('allocations', 'audit_logs')
       AND data_type = 'uuid')
ORDER BY table_name, ordinal_position;

-- Verify DECIMAL columns for monetary values
SELECT 
  table_name,
  column_name,
  data_type,
  numeric_precision,
  numeric_scale
FROM information_schema.columns
WHERE (table_name IN ('allocations', 'audit_logs')
       AND data_type = 'numeric')
ORDER BY table_name, ordinal_position;

-- ============================================================================
-- End of Verification Queries
-- ============================================================================
