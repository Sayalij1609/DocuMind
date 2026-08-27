import { useState } from "react";
import { uploadDocument } from "./services/api";


function App() {

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  const handleFileChange = (event) => {

    const file = event.target.files[0];

    setSelectedFile(file);
    setUploadResult(null);
    setError("");
  };


  const handleUpload = async () => {

    if (!selectedFile) {
      setError("Please select a document first.");
      return;
    }

    try {

      setLoading(true);
      setError("");

      const result = await uploadDocument(
        selectedFile
      );

      setUploadResult(result);

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);
    }
  };


  return (
    <div style={{ padding: "40px" }}>

      <h1>Nexora</h1>

      <p>
        Intelligent Document Processing
        & Understanding System
      </p>


      <input
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={handleFileChange}
      />


      <br />
      <br />


      <button
        onClick={handleUpload}
        disabled={loading}
      >
        {loading
          ? "Uploading..."
          : "Upload Document"
        }
      </button>


      {selectedFile && (
        <p>
          Selected: {selectedFile.name}
        </p>
      )}


      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}


      {uploadResult && (
        <div>

          <h2>Upload Successful</h2>

          <p>
            Document ID:
            {" "}
            {uploadResult.document_id}
          </p>

          <p>
            Filename:
            {" "}
            {uploadResult.filename}
          </p>

          <p>
            File Type:
            {" "}
            {uploadResult.file_type}
          </p>

          <p>
            File Size:
            {" "}
            {uploadResult.file_size}
            {" "}
            bytes
          </p>

          <p>
            Status:
            {" "}
            {uploadResult.status}
          </p>

        </div>
      )}

    </div>
  );
}


export default App;