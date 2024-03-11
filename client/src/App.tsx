import React, { useState, ChangeEvent } from "react";
import axios from "axios";
import {
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
} from "@mui/material";

const App: React.FC = () => {
  const url = "http://localhost:5000/";
  const [imageSrc, setImageSrc] = useState<string>(`${url}frame_feed`);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isCameraActive, setIsCameraActive] = useState<boolean>(true);
  const [youtubeUrl, setYoutubeUrl] = useState<string>("");
  const [descType, setDescType] = useState<string>("Live Camera");

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleYoutubeUrlChange = (event: ChangeEvent<HTMLInputElement>) => {
    setYoutubeUrl(event.target.value);
  };

  const handleImagePredict = async () => {
    if (!selectedFile) {
      alert("Please select a file first!");
      return;
    }

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
      const response = await axios.post(`${url}image_predict`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        responseType: "blob", // handling the binary image response
      });

      // Create a URL for the blob response and update the image source
      const imageUrl = URL.createObjectURL(response.data);
      setImageSrc(imageUrl);
      setIsCameraActive(false);
      await switchToImage();
    } catch (error) {
      console.error("Error uploading image:", error);
    }
  };

  const switchToCamera = async () => {
    try {
      await axios.post(`${url}switch_to_camera`);
      setImageSrc(`${url}frame_feed`);
      setIsCameraActive(true);
      setDescType("Live Camera");
    } catch (error) {
      alert(error + " Error switching to camera");
    }
  };

  const switchToYoutube = async () => {
    try {
      await axios.post(`${url}switch_to_youtube`, { youtubeUrl });
      setImageSrc(`${url}youtube_feed`);
      setIsCameraActive(false);
      setDescType("Youbute Video");
    } catch (error) {
      alert("Error switching to youtube");
    }
  };

  const switchToImage = async () => {
    try {
      await axios.post(`${url}switch_to_image`);
      setIsCameraActive(false);
      setDescType("Uploaded Image");
    } catch (error) {
      alert(error + " Error switching to image");
    }
  };

  return (
    <div className="p-4">
      {/* Add a text field for the image upload */}
      <TextField
        type="file"
        inputProps={{ accept: "image/*" }}
        onChange={handleFileChange}
        style={{ display: "block", margin: "10px 0" }}
      />
      <Button variant="contained" color="primary" onClick={handleImagePredict}>
        Upload and Predict
      </Button>

      {/* Add a text field for the youtube URL */}
      <TextField
        type="url"
        style={{ display: "block", margin: "10px 0" }}
        value={youtubeUrl}
        onChange={handleYoutubeUrlChange}
      />
      <Button
        variant="contained"
        color="primary"
        onClick={switchToYoutube}
        style={{ marginLeft: "10px" }}
      >
        Youtube predict
      </Button>

      {/* Add a button to switch to the camera feed */}
      {!isCameraActive && (
        <Button
          variant="contained"
          color="secondary"
          onClick={switchToCamera}
          style={{ marginLeft: "10px" }}
        >
          Switch to Camera
        </Button>
      )}

      <Card sx={{ maxWidth: 1080, marginTop: "20px" }}>
        <CardContent>
          <Typography gutterBottom variant="h5" component="div">
            {descType}
          </Typography>
        </CardContent>
        <img
          src={imageSrc}
          alt={descType}
          style={{ width: 1080, height: 720 }}
        />
      </Card>
    </div>
  );
};

export default App;
