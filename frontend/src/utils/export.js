import api from './api';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

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


export const exportTradesToPDF = async (strategyId = null) => {
    try {
        let url = '/trades/';
        if (strategyId) url += `?strategy_id=${strategyId}`;

        // BUG 24 FIX: Fetch instruments concurrently to map the ID to the Symbol
        const [tradesRes, instRes] = await Promise.all([
            api.get(url),
                                                       api.get('/instruments/')
        ]);

        const trades = tradesRes.data;
        const instruments = instRes.data;

        if (!trades || trades.length === 0) {
            alert("No trades to export.");
            return;
        }

        const doc = new jsPDF('landscape');
        doc.text("Reaper's Journal - Trade Export", 14, 15);

        const tableColumn = ["ID", "Status", "Pair", "Dir", "Entry", "Exit", "P&L", "R-Mult", "Emotion", "Date"];
        const tableRows = [];

        trades.forEach(t => {
            // Find the human-readable symbol
            const inst = instruments.find(i => i.id === t.instrument_id);
            const symbol = inst ? inst.symbol : t.instrument_id;

            const tradeData = [
                t.id,
                t.status,
                symbol, // Replaced t.instrument_id with symbol
                t.direction,
                t.entry_price,
                t.exit_price || '—',
                t.pnl_realized !== null ? `$${t.pnl_realized}` : '—',
                t.r_multiple || '—',
                t.emotion || '—',
                new Date(t.opened_at).toLocaleDateString()
            ];
            tableRows.push(tradeData);
        });

        doc.autoTable({
            head: [tableColumn],
            body: tableRows,
            startY: 20,
            theme: 'grid',
            styles: { fontSize: 8 },
            headStyles: { fillColor: [34, 211, 238] }
        });

        doc.save(`journal_export_${new Date().getTime()}.pdf`);
    } catch (err) {
        console.error("PDF Export failed", err);
        alert("Failed to export PDF.");
    }
};
