import { supabase } from "../supabase-client";


export const authenticatedFetch = async (url, options = {}) => {
    // Read the current access token immediately before the API call instead of
    // caching a JWT that may expire or be replaced when the session refreshes.
    const { data, error } = await supabase.auth.getSession();

    if (error) {
        throw new Error(`Unable to read authentication session: ${error.message}`);
    }

    const accessToken = data.session?.access_token;

    if (!accessToken) {
        throw new Error("You must be signed in to perform this action");
    }

    const headers = new Headers(options.headers);
    // placce the token in the header to the request
    // FastAPI extracts and validates this bearer token before protected routes run.
    headers.set("Authorization", `Bearer ${accessToken}`);

    return fetch(url, {
        ...options,
        headers,
    });
};