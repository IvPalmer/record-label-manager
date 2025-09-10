import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getTrack, updateTrack, deleteTrack } from '../api/tracks';
import { getArtists } from '../api/artists';
import { getReleases } from '../api/releases';
import { getLabels } from '../api/labels';
import TrackForm from './TrackForm';
import styles from './TrackDetail.module.css';

const TrackDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [track, setTrack] = useState(null);
  const [artists, setArtists] = useState([]);
  const [releases, setReleases] = useState([]);
  const [labels, setLabels] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [trackData, artistsData, releasesData, labelsData] = await Promise.all([
          getTrack(id),
          getArtists(),
          getReleases(),
          getLabels()
        ]);
        
        setTrack(trackData);
        setArtists(artistsData);
        setReleases(releasesData);
        setLabels(labelsData);
      } catch (err) {
        console.error('Error fetching track details:', err);
        setError(`Failed to load track: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleSave = async (updatedTrackData) => {
    setIsLoading(true);
    try {
      const result = await updateTrack(id, updatedTrackData);
      setTrack(result);
      setIsEditing(false);
      alert('Track updated successfully!');
    } catch (err) {
      console.error('Error updating track:', err);
      setError(`Failed to update track: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this track? This action cannot be undone.')) {
      setIsLoading(true);
      try {
        await deleteTrack(id);
        navigate('/tracks');
      } catch (err) {
        console.error('Error deleting track:', err);
        setError(`Failed to delete track: ${err.message}`);
        setIsLoading(false);
      }
    }
  };

  const getArtistName = (artistId) => {
    const artist = artists.find(a => a.id === artistId);
    return artist ? artist.project || artist.name : 'Unknown Artist';
  };

  const getReleaseName = (releaseId) => {
    const release = releases.find(r => r.id === releaseId);
    return release ? release.title : 'Unknown Release';
  };

  const getLabelName = (labelId) => {
    const label = labels.find(l => l.id === labelId);
    return label ? label.name : 'Unknown Label';
  };

  if (isLoading) return <div className={styles.loading}>Loading track details...</div>;
  if (error) return <div className={styles.error}>{error}</div>;
  if (!track) return <div className={styles.notFound}>Track not found</div>;

  return (
    <div className={styles.trackDetail}>
      {isEditing ? (
        <TrackForm
          track={track}
          onSave={handleSave}
          onCancel={() => setIsEditing(false)}
          artists={artists}
          releases={releases}
          labels={labels}
        />
      ) : (
        <>
          <div className={styles.header}>
            <button onClick={() => navigate('/tracks')} className={styles.backButton}>
              &larr; Back to Tracks
            </button>
            <h1>{track.title}</h1>
            <div className={styles.actions}>
              <button onClick={() => setIsEditing(true)} className={styles.editButton}>
                Edit
              </button>
              <button onClick={handleDelete} className={styles.deleteButton}>
                Delete
              </button>
            </div>
          </div>

          <div className={styles.trackInfo}>
            <div className={styles.section}>
              <h3>Track Information</h3>
              <div className={styles.infoGrid}>
                <div className={styles.infoItem}>
                  <span className={styles.label}>Title:</span>
                  <span className={styles.value}>{track.title}</span>
                </div>
                <div className={styles.infoItem}>
                  <span className={styles.label}>ISRC Code:</span>
                  <span className={styles.value}>{track.src_code || 'Not assigned'}</span>
                </div>
              </div>

              {track.audio_url && (
                <div className={styles.audioPreview}>
                  <h4>Audio Preview</h4>
                  <audio controls src={track.audio_url}>
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
            </div>

            <div className={styles.section}>
              <h3>Artists</h3>
              <div className={styles.infoGrid}>
                <div className={styles.infoItem}>
                  <span className={styles.label}>Main Artist:</span>
                  <span className={styles.value}>
                    {(() => {
                      const artist = artists.find(a => a.id === track.artist);
                      return artist ? (
                        <Link to={`/artists/${artist.id}`}>
                          {artist.project || artist.name}
                        </Link>
                      ) : 'Unknown';
                    })()}
                  </span>
                </div>
                
                {track.featuring_artists && track.featuring_artists.length > 0 && (
                  <div className={styles.infoItem}>
                    <span className={styles.label}>Featuring:</span>
                    <span className={styles.value}>
                      {track.featuring_artists.map((artistId, index) => {
                        const artist = artists.find(a => a.id === artistId);
                        return artist ? (
                          <span key={artist.id} className={styles.featuringArtist}>
                            <Link to={`/artists/${artist.id}`}>
                              {artist.project || artist.name}
                            </Link>
                            {index < track.featuring_artists.length - 1 ? ', ' : ''}
                          </span>
                        ) : 'Unknown';
                      })}
                    </span>
                  </div>
                )}
                
                {track.remix_artist && (
                  <div className={styles.infoItem}>
                    <span className={styles.label}>Remixed by:</span>
                    <span className={styles.value}>
                      {(() => {
                        const remixArtist = artists.find(a => a.id === track.remix_artist);
                        return remixArtist ? (
                          <Link to={`/artists/${remixArtist.id}`}>
                            {remixArtist.project || remixArtist.name}
                          </Link>
                        ) : 'Unknown';
                      })()}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className={styles.section}>
              <h3>Release Information</h3>
              <div className={styles.infoGrid}>
                <div className={styles.infoItem}>
                  <span className={styles.label}>Release:</span>
                  <span className={styles.value}>
                    {(() => {
                      const release = releases.find(r => r.id === track.release);
                      return release ? (
                        <Link to={`/releases/${release.id}`}>
                          {release.title}
                        </Link>
                      ) : 'Unknown';
                    })()}
                  </span>
                </div>
                <div className={styles.infoItem}>
                  <span className={styles.label}>Label:</span>
                  <span className={styles.value}>
                    {(() => {
                      const label = labels.find(l => l.id === track.label);
                      return label ? (
                        <Link to={`/labels/${label.id}`}>
                          {label.name}
                        </Link>
                      ) : 'Unknown';
                    })()}
                  </span>
                </div>
              </div>
            </div>

            <div className={styles.section}>
              <h3>Streaming Information</h3>
              <div className={styles.infoGrid}>
                <div className={styles.infoItem}>
                  <span className={styles.label}>Streaming Single:</span>
                  <span className={`${styles.value} ${track.is_streaming_single ? styles.streamingTrue : styles.streamingFalse}`}>
                    {track.is_streaming_single ? 'Yes' : 'No'}
                  </span>
                </div>
                
                {track.streaming_release_date && (
                  <div className={styles.infoItem}>
                    <span className={styles.label}>Streaming Release Date:</span>
                    <span className={styles.value}>{track.streaming_release_date}</span>
                  </div>
                )}
              </div>
            </div>

            {track.tags && track.tags.length > 0 && (
              <div className={styles.section}>
                <h3>Tags</h3>
                <div className={styles.tags}>
                  {track.tags.map(tag => (
                    <span key={tag} className={styles.tag}>{tag}</span>
                  ))}
                </div>
              </div>
            )}
            
            <div className={styles.section}>
              <h3>Metadata</h3>
              <div className={styles.infoGrid}>
                {track.created_at && (
                  <div className={styles.infoItem}>
                    <span className={styles.label}>Created At:</span>
                    <span className={styles.value}>
                      {new Date(track.created_at).toLocaleString()}
                    </span>
                  </div>
                )}
                
                {track.updated_at && (
                  <div className={styles.infoItem}>
                    <span className={styles.label}>Updated At:</span>
                    <span className={styles.value}>
                      {new Date(track.updated_at).toLocaleString()}
                    </span>
                  </div>
                )}
                
                {track.duration && (
                  <div className={styles.infoItem}>
                    <span className={styles.label}>Duration:</span>
                    <span className={styles.value}>{track.duration}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TrackDetail;
