export const formatCurrency = (value, currency = 'USD') => {
    if (value === null || value === undefined) return '—';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
    }).format(value);
};

export const formatPips = (value) => {
    if (value === null || value === undefined) return '—';
    // Forex standard is usually 1 decimal place for fractional pips
    return parseFloat(value).toFixed(1);
};

export const formatIST = (utcDateString) => {
    if (!utcDateString) return '—';
    const date = new Date(utcDateString);
    return date.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        dateStyle: 'medium',
        timeStyle: 'short'
    });
};
