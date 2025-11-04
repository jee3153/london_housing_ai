import type { MlflowRunResponse } from "../../types/mlflow";

type ModelPerformanceProps = {
  latestRun: MlflowRunResponse | null;
};

export default function ModelPerformance({ latestRun }: ModelPerformanceProps) {
  const metrics = latestRun?.data.metrics;
  const params = latestRun?.data.params;

  return (
    <section>
      <h2 className="text-lg font-semibold">Model Performance Board</h2>
      {metrics ? (
        <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-md border bg-card p-4 shadow-sm">
            <dt className="text-sm text-muted-foreground">RMSE</dt>
            <dd className="text-2xl font-medium">{metrics.rmse.toFixed(2)}</dd>
          </div>
          <div className="rounded-md border bg-card p-4 shadow-sm">
            <dt className="text-sm text-muted-foreground">Validation RMSE</dt>
            <dd className="text-2xl font-medium">{metrics.val_rmse.toFixed(2)}</dd>
          </div>
        </dl>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">No MLflow runs found yet.</p>
      )}
      {params && (
        <div className="mt-6 rounded-md border bg-card p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-muted-foreground">Training Parameters</h3>
          <ul className="mt-2 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
            {Object.entries(params).map(([key, value]) => (
              <li key={key} className="flex justify-between gap-2">
                <span className="text-muted-foreground">{key}</span>
                <span className="font-medium">{value}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
