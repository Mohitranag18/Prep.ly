import React, { useState } from 'react';
import { generate_practice_questions } from '../api/endpoints'

function GetPracticeQues() {
  const [videoUrl, setVideoUrl] = useState('');
  const [timestamp, setTimestamp] = useState('');
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setQuestions([]);
    setError('');

    try {
      const data = await generate_practice_questions(videoUrl, parseInt(timestamp));
      if (data.questions) {
        setQuestions(data.questions);
      } else {
        setError(data.error || 'No questions returned.');
      }
    } catch (err) {
      setError('Failed to fetch questions.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Generate Practice Questions</h2>

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="text"
          placeholder="YouTube Video URL"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          className="w-full p-2 border rounded"
          required
        />
        <input
          type="number"
          placeholder="Timestamp (in seconds)"
          value={timestamp}
          onChange={(e) => setTimestamp(e.target.value)}
          className="w-full p-2 border rounded"
          required
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {loading ? 'Generating...' : 'Get Questions'}
        </button>
      </form>

      {error && <p className="text-red-500 mt-4">{error}</p>}

      {questions.length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-lg font-semibold">Practice Questions:</h3>
          <ul className="list-disc pl-5 space-y-2">
            {questions.map((q, index) => (
              <li key={index}>
                <a
                  href={q.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {q.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default GetPracticeQues;
