import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../utils/api';

export default function StrategyDetail() {
    const { id } = useParams();
    const [strategy, setStrategy] = useState(null);
    const [rules, setRules] = useState([]);
    const [deposits, setDeposits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Rule Form State
    const [isRuleFormOpen, setIsRuleFormOpen] = useState(false);
    const [newRule, setNewRule] = useState({
        rule_type: 'entry',
        label: '',
        params: '{}',
        is_required: true,
    });

    // Deposit Form State
    const [isDepositFormOpen, setIsDepositFormOpen] = useState(false);
    const [newDeposit, setNewDeposit] = useState({
        amount: '',
        kind: 'deposit',
        date: new Date().toISOString().split('T')[0],
                                                 note: ''
    });

    const fetchData = async () => {
        try {
            const [stratRes, rulesRes, depositsRes] = await Promise.all([
                api.get(`/strategies/`),
                                                                        api.get(`/strategies/${id}/rules`),
                                                                        api.get(`/strategies/${id}/deposits`)
            ]);

            const foundStrategy = stratRes.data.find(s => s.id === parseInt(id));
            if (!foundStrategy) throw new Error("Strategy not found");

            setStrategy(foundStrategy);
            setRules(rulesRes.data);
            setDeposits(depositsRes.data);
        } catch (err) {
            setError('Failed to load strategy details.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [id]);

    const handleCreateRule = async (e) => {
        e.preventDefault();
        try {
            let parsedParams = {};
            if (newRule.params.trim()) {
                try {
                    parsedParams = JSON.parse(newRule.params);
                } catch (e) {
                    alert("Invalid JSON format for params");
                    return;
                }
            }

            const payload = {
                ...newRule,
                params: parsedParams,
                sort_order: rules.length
            };

            await api.post(`/strategies/${id}/rules`, payload);
            setIsRuleFormOpen(false);
            setNewRule({ rule_type: 'entry', label: '', params: '{}', is_required: true });
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to create rule');
        }
    };

    const handleDeleteRule = async (ruleId) => {
        if (!window.confirm("Delete this rule?")) return;
        try {
            await api.delete(`/strategies/${id}/rules/${ruleId}`);
            fetchData();
        } catch (err) {
            alert('Failed to delete rule');
        }
    };

    const handleCreateDeposit = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...newDeposit, amount: parseFloat(newDeposit.amount) };
            await api.post(`/strategies/${id}/deposits`, payload);
            setIsDepositFormOpen(false);
            setNewDeposit({ amount: '', kind: 'deposit', date: new Date().toISOString().split('T')[0], note: '' });
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to log transaction');
        }
    };

    const handleDeleteDeposit = async (depositId) => {
        if (!window.confirm("Delete this transaction?")) return;
        try {
            await api.delete(`/strategies/${id}/deposits/${depositId}`);
            fetchData();
        } catch (err) {
            alert('Failed to delete transaction');
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>Loading...</div>;
    if (error) return <div style={{ padding: '2rem', color: '#ef4444' }}>{error}</div>;

    const totalBalance = deposits.reduce((acc, dep) => {
        return dep.kind === 'deposit' ? acc + parseFloat(dep.amount) : acc - parseFloat(dep.amount);
    }, 0);

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
        <Link to="/strategies" style={{ color: '#94a3b8', textDecoration: 'none', marginBottom: '1rem', display: 'inline-block' }}>
        ← Back to Strategies
        </Link>
        <h2 style={{ margin: '0 0 0.5rem 0', color: '#22d3ee' }}>{strategy.name}</h2>
        {strategy.description && <p style={{ color: '#cbd5e1', marginTop: 0 }}>{strategy.description}</p>}
        </div>

        <div style={{ textAlign: 'right', background: '#1e293b', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Funding Balance</div>
        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: totalBalance >= 0 ? '#22c55e' : '#ef4444' }}>
        ${totalBalance.toFixed(2)}
        </div>
        </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>Strategy Rules</h3>
        <button
        onClick={() => setIsRuleFormOpen(!isRuleFormOpen)}
        style={{ background: '#334155', color: '#f8fafc', padding: '0.5rem 1rem', border: 'none', cursor: 'pointer', borderRadius: '4px' }}
        >
        {isRuleFormOpen ? 'Cancel' : '+ Add Rule'}
        </button>
        </div>

        {isRuleFormOpen && (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <form onSubmit={handleCreateRule} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
            <select
            value={newRule.rule_type}
            onChange={e => setNewRule({...newRule, rule_type: e.target.value})}
            style={{ padding: '0.5rem', flex: 1 }}
            >
            <option value="entry">Entry Rule</option>
            <option value="exit">Exit Rule</option>
            <option value="risk">Risk Rule</option>
            <option value="filter">Filter</option>
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1' }}>
            <input
            type="checkbox"
            checked={newRule.is_required}
            onChange={e => setNewRule({...newRule, is_required: e.target.checked})}
            />
            Required
            </label>
            </div>

            <input
            placeholder="Rule Label (e.g., Price > 200 EMA)"
            value={newRule.label}
            onChange={e => setNewRule({...newRule, label: e.target.value})}
            required
            style={{ padding: '0.5rem' }}
            />

            <div>
            <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Parameters (JSON)</label>
            <textarea
            placeholder='{"threshold": 200}'
        value={newRule.params}
        onChange={e => setNewRule({...newRule, params: e.target.value})}
        style={{ padding: '0.5rem', width: '100%', minHeight: '60px', fontFamily: 'monospace' }}
        />
        </div>

        <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px' }}>
        Save Rule
        </button>
        </form>
        </div>
        )}

        {rules.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No rules configured yet.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '3rem' }}>
            {rules.map(rule => (
                <div key={rule.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#1e293b', padding: '1rem', borderRadius: '4px' }}>
                <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                <span style={{
                    fontSize: '0.75rem',
                    textTransform: 'uppercase',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    background: rule.rule_type === 'risk' ? '#ef4444' : rule.rule_type === 'entry' ? '#22c55e' : '#3b82f6',
                    color: 'white'
                }}>
                {rule.rule_type}
                </span>
                <strong style={{ color: rule.is_required ? '#f8fafc' : '#94a3b8' }}>{rule.label}</strong>
                </div>
                {Object.keys(rule.params).length > 0 && (
                    <pre style={{ margin: '0.5rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8', background: '#0f172a', padding: '0.5rem', borderRadius: '4px' }}>
                    {JSON.stringify(rule.params)}
                    </pre>
                )}
                </div>
                <button onClick={() => handleDeleteRule(rule.id)} style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem' }}>
                ×
                </button>
                </div>
            ))}
            </div>
        )}

        <hr style={{ borderColor: '#334155', margin: '2rem 0' }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>Funding History</h3>
        <button
        onClick={() => setIsDepositFormOpen(!isDepositFormOpen)}
        style={{ background: '#334155', color: '#f8fafc', padding: '0.5rem 1rem', border: 'none', cursor: 'pointer', borderRadius: '4px' }}
        >
        {isDepositFormOpen ? 'Cancel' : '+ Log Transaction'}
        </button>
        </div>

        {isDepositFormOpen && (
            <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <form onSubmit={handleCreateDeposit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
            <select
            value={newDeposit.kind}
            onChange={e => setNewDeposit({...newDeposit, kind: e.target.value})}
            style={{ padding: '0.5rem', flex: 1 }}
            >
            <option value="deposit">Deposit</option>
            <option value="withdrawal">Withdrawal</option>
            </select>
            <input
            type="date"
            value={newDeposit.date}
            onChange={e => setNewDeposit({...newDeposit, date: e.target.value})}
            required
            style={{ padding: '0.5rem', flex: 1 }}
            />
            </div>

            <input
            type="number"
            step="0.01"
            placeholder="Amount"
            value={newDeposit.amount}
            onChange={e => setNewDeposit({...newDeposit, amount: e.target.value})}
            required
            style={{ padding: '0.5rem' }}
            />

            <input
            placeholder="Notes (optional)"
            value={newDeposit.note}
            onChange={e => setNewDeposit({...newDeposit, note: e.target.value})}
            style={{ padding: '0.5rem' }}
            />

            <button type="submit" style={{ background: '#22d3ee', color: '#0f172a', padding: '0.5rem', fontWeight: 'bold', border: 'none', cursor: 'pointer', borderRadius: '4px' }}>
            Save Transaction
            </button>
            </form>
            </div>
        )}

        {deposits.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No funding history.</p>
        ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '3rem' }}>
            {deposits.map(dep => (
                <div key={dep.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#1e293b', padding: '1rem', borderRadius: '4px', borderLeft: `4px solid ${dep.kind === 'deposit' ? '#22c55e' : '#ef4444'}` }}>
                <div>
                <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{dep.date}</div>
                <div style={{ color: '#f8fafc', fontWeight: 'bold' }}>
                {dep.kind === 'deposit' ? '+' : '-'}${parseFloat(dep.amount).toFixed(2)}
                </div>
                {dep.note && <div style={{ color: '#cbd5e1', fontSize: '0.875rem', marginTop: '0.25rem' }}>{dep.note}</div>}
                </div>
                <button onClick={() => handleDeleteDeposit(dep.id)} style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem' }}>
                ×
                </button>
                </div>
            ))}
            </div>
        )}

        </div>
    );
}
