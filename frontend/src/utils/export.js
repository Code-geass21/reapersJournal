import api from './api';

export const exportTradesToCSV = async (strategyId = null) => {
    try {
        let url = '/trades/';
        if (strategyId) {
            url += `?strategy_id=${strategyId}`;
        }

        const res = await api.get(url);
        const trades = res.data;

        if (!trades || trades.length === 0) {
            alert("No trades to export.");
            return;
        }

        // Define headers
        const headers = [
            "ID", "Status", "Direction", "Entry Price", "Exit Price",
            "Size", "Realized P&L", "R-Multiple", "Emotion", "Tags", "Opened At"
        ];

        // Map data rows
        const rows = trades.map(t => [
            t.id,
            t.status,
            t.direction,
            t.entry_price,
            t.exit_price || '',
            t.size,
            t.pnl_realized || '',
            t.r_multiple || '',
            t.emotion || '',
            t.tags ? t.tags.join(';') : '',
                                new Date(t.opened_at).toISOString()
        ]);

        // Build CSV string
        const csvContent = [
            headers.join(','),
            ...rows.map(e => e.join(','))
        ].join('\n');

        // Trigger download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const urlObj = URL.createObjectURL(blob);
        link.setAttribute("href", urlObj);
        link.setAttribute("download", `journal_export_${new Date().getTime()}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (err) {
        console.error("Export failed", err);
        alert("Failed to export data.");
    }
};
