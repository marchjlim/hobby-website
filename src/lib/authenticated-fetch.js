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

    const sendRequest = (token) => {
        const headers = new Headers(options.headers);
        // FastAPI extracts and validates this bearer token before protected routes run.
        headers.set("Authorization", `Bearer ${token}`);
        return fetch(url, {
            ...options,
            headers,
        });
    };

    const response = await sendRequest(accessToken);
    if (response.status !== 401) {
        return response;
    }

    // A locally cached session can briefly contain an expired access token.
    // Refresh once and retry; a second 401 is returned to the caller unchanged.
    const { data: refreshedData, error: refreshError } =
        await supabase.auth.refreshSession();
    const refreshedToken = refreshedData.session?.access_token;
    if (refreshError || !refreshedToken) {
        return response;
    }

    return sendRequest(refreshedToken);
};
