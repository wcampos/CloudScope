import type { ResourceRow } from '@/types/resource';

interface DataTableProps {
  data: ResourceRow[];
}

export default function DataTable({ data }: DataTableProps) {
  if (!data?.length) return null;
  const headers = Object.keys(data[0]);

  return (
    <div className="table-responsive" style={{ margin: 0 }}>
      <table className="table-modern">
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {headers.map((h) => (
                <td key={h}>{String(row[h] ?? '-')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
