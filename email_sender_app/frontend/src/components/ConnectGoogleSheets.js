import React, { useState } from 'react';
import axios from 'axios';

function ConnectGoogleSheets() {
  const [credentialsFile, setCredentialsFile] = useState(null);

  const connectGoogleSheets = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('credentials_file', credentialsFile);
    await axios.post('/connect_google_sheets/', formData);
    alert('Google Sheets connected successfully');
  };

  return (
    <form onSubmit={connectGoogleSheets}>
      <input type="file" onChange={(e) => setCredentialsFile(e.target.files[0])} />
      <button type="submit">Connect Google Sheets</button>
    </form>
  );
}

export default ConnectGoogleSheets;