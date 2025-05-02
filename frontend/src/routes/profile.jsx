import React, { useEffect, useState } from 'react';
import { user_video_inputs } from '../api/endpoints';

function Profile() {
  const [videos, setVideos] = useState([]);

  const get_videos_data = async () => {
    try {
      const data = await user_video_inputs();
      setVideos(data);
    } catch (err) {
      alert('Failed to fetch video input.');
    }
  };

  useEffect(() => {
    get_videos_data();
  }, []);

  return (
    <div>
      <h2 className='py-6'>My Watched Videos</h2>
      {videos.length === 0 ? (
        <p>No video inputs found.</p>
      ) : (
        <ul>
          {videos.map((video) => (
            <li key={video.slug}>
              <a href={video.video_url}><p><strong>URL:</strong> {video.video_url}</p></a>
              <p><strong>Watched Till:</strong> {video.watched_till} seconds</p>
              <p><strong>Slug:</strong> {video.slug}</p>
              <hr />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Profile;
