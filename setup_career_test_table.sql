-- Create CareerTestResults table
CREATE TABLE IF NOT EXISTS "CareerTestResults" (
    "id" UUID PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES "Users"("id") ON DELETE CASCADE,
    "answers" JSONB NOT NULL,
    "results" JSONB NOT NULL,
    "personality_insights" JSONB,
    "plan_type" TEXT NOT NULL DEFAULT 'free',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS "idx_career_test_results_user_id" ON "CareerTestResults" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_career_test_results_created_at" ON "CareerTestResults" ("created_at");

-- Add RLS (Row Level Security) policies
ALTER TABLE "CareerTestResults" ENABLE ROW LEVEL SECURITY;

-- Policy to allow users to see only their own test results
CREATE POLICY "Users can view their own test results" 
ON "CareerTestResults" FOR SELECT 
USING (auth.uid() = user_id);

-- Policy to allow users to insert their own test results
CREATE POLICY "Users can insert their own test results" 
ON "CareerTestResults" FOR INSERT 
WITH CHECK (auth.uid() = user_id);