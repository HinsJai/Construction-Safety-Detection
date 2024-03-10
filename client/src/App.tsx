import React, { ChangeEvent, useState, useEffect } from "react";
import axios from "axios";
import {
  Button,
  Card,
  CardContent,
  CardMedia,
  Typography,
} from "@mui/material";

const App: React.FC = () => {
  const url = "http://localhost:5000/";
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isCameraActive, setIsCameraActive] = useState<boolean>(true);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string>("");

  useEffect(() => {}, [uploadedImageUrl, isCameraActive]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      const formData = new FormData();
      formData.append("file", selectedFile);
      try {
        const response = await axios.post(`${url}upload`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
        alert("File uploaded successfully");
        const { filename } = response.data;
        console.log("Uploaded file: ", filename);
        setUploadedImageUrl(`${url}uploaded/${filename}`);
        setIsCameraActive(false);
      } catch (error) {
        alert(error + " Error uploading file");
      }
    }
  };

  const switchToCamera = async () => {
    try {
      await axios.post(`${url}switch_to_camera`);
      setIsCameraActive(true);
    } catch (error) {
      alert(error + " Error switching to camera");
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <Button variant="contained" color="primary" onClick={handleUpload}>
        Upload
      </Button>
      {!isCameraActive && ( // Conditionally render the switch to camera button
        <Button variant="contained" color="secondary" onClick={switchToCamera}>
          Switch to Camera
        </Button>
      )}

      <Card>
        <CardContent>
          <Typography gutterBottom variant="h5" component="div">
            {isCameraActive ? "Live Camera Feed" : "Uploaded Image"}
          </Typography>
        </CardContent>
        <CardMedia
          component="img"
          image={`${url}frame_feed`}
          alt={isCameraActive ? "Live Camera Feed" : "Uploaded Image"}
          sx={{ width: 900, height: 600 }}
        />
      </Card>
    </div>
  );
};

export default App;
