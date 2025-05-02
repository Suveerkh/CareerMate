-- Create UserSubscriptions table
CREATE TABLE IF NOT EXISTS "UserSubscriptions" (
    "id" UUID PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES "Users"("id") ON DELETE CASCADE,
    "feature_id" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT TRUE,
    "auto_renew" BOOLEAN NOT NULL DEFAULT TRUE,
    "purchase_date" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "expiry_date" TIMESTAMP WITH TIME ZONE NOT NULL,
    "price" DECIMAL(10, 2) NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS "idx_user_subscriptions_user_id" ON "UserSubscriptions" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_user_subscriptions_feature_id" ON "UserSubscriptions" ("feature_id");
CREATE INDEX IF NOT EXISTS "idx_user_subscriptions_expiry_date" ON "UserSubscriptions" ("expiry_date");

-- Add RLS (Row Level Security) policies
ALTER TABLE "UserSubscriptions" ENABLE ROW LEVEL SECURITY;

-- Policy to allow users to see only their own subscriptions
CREATE POLICY "Users can view their own subscriptions" 
ON "UserSubscriptions" FOR SELECT 
USING (auth.uid() = user_id);

-- Create SubscriptionTransactions table for payment history
CREATE TABLE IF NOT EXISTS "SubscriptionTransactions" (
    "id" UUID PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES "Users"("id") ON DELETE CASCADE,
    "subscription_id" UUID REFERENCES "UserSubscriptions"("id") ON DELETE SET NULL,
    "feature_id" TEXT NOT NULL,
    "amount" DECIMAL(10, 2) NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "status" TEXT NOT NULL,
    "payment_method" TEXT,
    "transaction_date" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS "idx_subscription_transactions_user_id" ON "SubscriptionTransactions" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_subscription_transactions_subscription_id" ON "SubscriptionTransactions" ("subscription_id");

-- Add RLS (Row Level Security) policies
ALTER TABLE "SubscriptionTransactions" ENABLE ROW LEVEL SECURITY;

-- Policy to allow users to see only their own transactions
CREATE POLICY "Users can view their own transactions" 
ON "SubscriptionTransactions" FOR SELECT 
USING (auth.uid() = user_id);