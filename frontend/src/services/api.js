// API service
const API_BASE_URL = "http://localhost:8000";

export async function checkHealth() {
    const response = await fetch(
        `${API_BASE_URL}/health`
    );

    if (!response.ok) {
        throw new Error("Backend health check failed");
    }

    return response.json();
}


export async function uploadDocument(file) {
    const formData = new FormData();

    formData.append("file", file);

    const response = await fetch(
        `${API_BASE_URL}/api/documents/upload`,
        {
            method: "POST",
            body: formData
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || "Document upload failed"
        );
    }

    return data;
}