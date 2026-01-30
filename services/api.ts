import axios from 'axios';
import { VideoData } from '../types';

// Detect environment: 
// On Vercel (Production), we use relative path '/api' which routes to api/index.py
// On Local, we use 'http://localhost:8000/api' if the user is running the python server separately,
// OR if using `vite proxy`, relative path would work too. 
// For safety, we check if we are on localhost.
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocal ? 'http://localhost:8000/api' : '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 8000, // Increased timeout for serverless cold starts
});

// Mock data for demo/fallback purposes
const MOCK_DATA: VideoData = {
  id: 'demo-video-1',
  title: 'Backend Unavailable: Showing Demo Video (Big Buck Bunny)',
  thumbnail: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Big_buck_bunny_poster_big.jpg/800px-Big_buck_bunny_poster_big.jpg',
  duration: 596,
  platform: 'Demo Mode',
  download_url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
  ext: 'mp4',
  isMock: true,
};

export const fetchVideoInfo = async (url: string): Promise<VideoData> => {
  try {
    const response = await apiClient.get<VideoData>('/info', {
      params: { url },
    });
    return response.data;
  } catch (error) {
    console.warn('Backend unavailable or Vercel timeout, falling back to demo mode:', error);
    
    // Simulate network delay for realistic UX
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Return mock data so the UI can be tested/viewed
    return {
      ...MOCK_DATA,
      // Update title to reflect the user's input so it feels responsive
      title: `DEMO RESULT: ${url.slice(0, 30)}${url.length > 30 ? '...' : ''}`,
    };
  }
};

export const getDownloadLink = (videoData: VideoData): string => {
  // If we are in mock mode, return the direct URL (the proxy won't work)
  if (videoData.isMock) {
    return videoData.download_url;
  }

  // Construct the proxy URL
  const params = new URLSearchParams({
    url: videoData.download_url,
    title: videoData.title,
    ext: videoData.ext,
  });
  return `${API_BASE_URL}/download?${params.toString()}`;
};