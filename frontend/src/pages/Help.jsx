import { useState, useEffect } from 'react';
import api from '../utils/api';
import ReactMarkdown from 'react-markdown';

export default function Help() {
    const [articles, setArticles] = useState([]);
    const [selectedSlug, setSelectedSlug] = useState(null);
    const [articleContent, setArticleContent] = useState(null);
    const [loading, setLoading] = useState(true);

    // Fetch the list of topics on load
    useEffect(() => {
        const fetchList = async () => {
            try {
                const res = await api.get('/help/');
                setArticles(res.data);
                if (res.data.length > 0) {
                    setSelectedSlug(res.data[0].slug); // Auto-select the first article
                }
            } catch (err) {
                console.error("Failed to fetch help articles", err);
            } finally {
                setLoading(false);
            }
        };
        fetchList();
    }, []);

    // Fetch the full markdown content when a topic is selected
    useEffect(() => {
        if (!selectedSlug) return;
        const fetchArticle = async () => {
            try {
                const res = await api.get(`/help/${selectedSlug}`);
                setArticleContent(res.data);
            } catch (err) {
                console.error("Failed to fetch article", err);
            }
        };
        fetchArticle();
    }, [selectedSlug]);

    if (loading) return <div style={{ padding: '2rem', color: '#94a3b8' }}>Loading Help Center...</div>;

    return (
        <div style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto', display: 'flex', gap: '2rem' }}>

        {/* Sidebar Navigation */}
        <div style={{ width: '250px', background: '#1e293b', padding: '1rem', borderRadius: '8px', alignSelf: 'flex-start' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#f8fafc', fontSize: '1rem', textTransform: 'uppercase' }}>Help Topics</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {articles.map(a => (
            <button
            key={a.slug}
            onClick={() => setSelectedSlug(a.slug)}
            style={{
                background: selectedSlug === a.slug ? '#334155' : 'transparent',
                color: selectedSlug === a.slug ? '#22d3ee' : '#cbd5e1',
                border: 'none',
                padding: '0.75rem',
                textAlign: 'left',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: selectedSlug === a.slug ? 'bold' : 'normal',
                transition: 'background 0.2s'
            }}
            >
            {a.title}
            </button>
        ))}
        </div>
        </div>

        {/* Article Markdown Content */}
        <div style={{ flex: 1, background: '#1e293b', padding: '2.5rem', borderRadius: '8px' }}>
        {articleContent ? (
            <div style={{ color: '#f8fafc', lineHeight: '1.7' }}>
            <h2 style={{ margin: '0 0 1.5rem 0', color: '#22d3ee', borderBottom: '1px solid #334155', paddingBottom: '1rem' }}>
            {articleContent.title}
            </h2>
            {/* react-markdown safely converts the string to HTML */}
            <ReactMarkdown>{articleContent.content}</ReactMarkdown>
            </div>
        ) : (
            <div style={{ color: '#94a3b8' }}>Select a topic to read.</div>
        )}
        </div>
        </div>
    );
}
