import React, { useState } from 'react';
import axios from 'axios';

function ScheduleEmails() {
  const [scheduleTime, setScheduleTime] = useState('');

  const scheduleEmails = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('schedule_time', scheduleTime);
    await axios.post('/schedule_emails/', formData);
    alert('Emails scheduled successfully');
  };

  return (
    <form onSubmit={scheduleEmails}>
      <input type="time" value={scheduleTime} onChange={(e) => setScheduleTime(e.target.value)} />
      <button type="submit">Schedule Emails</button>
    </form>
  );
}

export default ScheduleEmails;