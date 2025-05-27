import { createClient } from "@supabase/supabase-js"

export const supabase = createClient(
    "https://dnkcamwwdiewdwoyaebl.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRua2NhbXd3ZGlld2R3b3lhZWJsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyNDg2ODksImV4cCI6MjA2MzgyNDY4OX0.OG2J-5GFcaub5RFSBRV9SA0vuoKPUjUg555qxeYvuk8"
)