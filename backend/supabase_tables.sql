-- Chef Bot Supabase Tables
-- This SQL script updates existing tables to use UUIDs

-- First, disable Row Level Security to allow modifications
ALTER TABLE IF EXISTS public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.ingredients DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.saved_recipes DISABLE ROW LEVEL SECURITY;

-- -- Create a backup of existing tables
-- CREATE TABLE IF NOT EXISTS public.users_backup AS SELECT * FROM public.users;
-- CREATE TABLE IF NOT EXISTS public.ingredients_backup AS SELECT * FROM public.ingredients;
-- CREATE TABLE IF NOT EXISTS public.saved_recipes_backup AS SELECT * FROM public.saved_recipes;

-- Drop existing tables (if they exist)
DROP TABLE IF EXISTS public.ingredients;
DROP TABLE IF EXISTS public.saved_recipes;
DROP TABLE IF EXISTS public.users;

-- Recreate Users Table with UUID
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT auth.uid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    picture VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on users table
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_google_id ON public.users(google_id);

-- Recreate Ingredients Table with UUID
CREATE TABLE public.ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    quantity FLOAT DEFAULT 1.0,
    unit VARCHAR(50) DEFAULT 'pieces',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE
);

-- Create index on ingredients table
CREATE INDEX idx_ingredients_user_id ON public.ingredients(user_id);

-- Recreate Saved Recipes Table with UUID
CREATE TABLE public.saved_recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_name VARCHAR(255) NOT NULL,
    ingredients_required JSONB NOT NULL,
    missing_ingredients JSONB DEFAULT '[]'::JSONB,
    instructions JSONB NOT NULL,
    difficulty_level VARCHAR(50),
    cooking_time VARCHAR(50),
    servings INTEGER DEFAULT 2,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE
);

-- Create index on saved_recipes table
CREATE INDEX idx_saved_recipes_user_id ON public.saved_recipes(user_id);

-- First, disable Row Level Security for initial data loading
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredients DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_recipes DISABLE ROW LEVEL SECURITY;

-- Create a function for data migration that bypasses RLS
CREATE OR REPLACE FUNCTION migrate_data_to_uuid_tables()
RETURNS VOID AS $$
DECLARE
    user_record RECORD;
    new_user_id UUID;
    ingredient_record RECORD;
    recipe_record RECORD;
BEGIN
    -- Migrate users data
    FOR user_record IN SELECT * FROM public.users_backup LOOP
        -- Generate a new UUID for each user
        new_user_id := gen_random_uuid();
        
        -- Insert user with new UUID
        INSERT INTO public.users (id, email, name, picture, google_id, is_active, created_at, updated_at)
        VALUES (
            new_user_id,
            user_record.email,
            user_record.name,
            user_record.picture,
            user_record.google_id,
            user_record.is_active,
            user_record.created_at,
            user_record.updated_at
        );
        
        -- Migrate ingredients for this user
        FOR ingredient_record IN 
            SELECT * FROM public.ingredients_backup 
            WHERE user_id = user_record.id::text OR user_id = user_record.id
        LOOP
            INSERT INTO public.ingredients (
                id, name, quantity, unit, created_at, updated_at, user_id
            ) VALUES (
                gen_random_uuid(),
                ingredient_record.name,
                ingredient_record.quantity,
                ingredient_record.unit,
                ingredient_record.created_at,
                ingredient_record.updated_at,
                new_user_id
            );
        END LOOP;
        
        -- Migrate saved recipes for this user
        FOR recipe_record IN 
            SELECT * FROM public.saved_recipes_backup 
            WHERE user_id = user_record.id::text OR user_id = user_record.id
        LOOP
            INSERT INTO public.saved_recipes (
                id, recipe_name, ingredients_required, missing_ingredients,
                instructions, difficulty_level, cooking_time, servings,
                notes, created_at, updated_at, user_id
            ) VALUES (
                gen_random_uuid(),
                recipe_record.recipe_name,
                recipe_record.ingredients_required,
                recipe_record.missing_ingredients,
                recipe_record.instructions,
                recipe_record.difficulty_level,
                recipe_record.cooking_time,
                recipe_record.servings,
                recipe_record.notes,
                recipe_record.created_at,
                recipe_record.updated_at,
                new_user_id
            );
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Data migration completed successfully';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Execute the data migration function
SELECT migrate_data_to_uuid_tables();

-- Clean up backup tables after successful migration
-- Uncomment these lines after verifying the migration was successful
-- DROP TABLE IF EXISTS public.users_backup;
-- DROP TABLE IF EXISTS public.ingredients_backup;
-- DROP TABLE IF EXISTS public.saved_recipes_backup;

-- After data migration, enable Row Level Security (RLS)
-- Uncomment these lines after initial data load
-- ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.saved_recipes ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can view their own data" 
ON public.users FOR SELECT 
USING (auth.uid() = id);

CREATE POLICY "Users can update their own data" 
ON public.users FOR UPDATE 
USING (auth.uid() = id);

-- Create policies for ingredients table
CREATE POLICY "Users can view their own ingredients" 
ON public.ingredients FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own ingredients" 
ON public.ingredients FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own ingredients" 
ON public.ingredients FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own ingredients" 
ON public.ingredients FOR DELETE 
USING (auth.uid() = user_id);

-- Create policies for saved_recipes table
CREATE POLICY "Users can view their own recipes" 
ON public.saved_recipes FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own recipes" 
ON public.saved_recipes FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own recipes" 
ON public.saved_recipes FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own recipes" 
ON public.saved_recipes FOR DELETE 
USING (auth.uid() = user_id);
