import { Link } from 'components/Link';
import { ElectricityModeType } from 'types';
import { sourceLinkMapping } from 'utils/constants';

import ProductionSourceLegend from './ProductionSourceLegend';
import { extractLinkFromSource } from './utils';

export function DataSources({
  title,
  icon,
  sources,
  sourceToProductionSources,
}: {
  title: string;
  icon: React.ReactNode;
  sources?: string[];
  sourceToProductionSources?: Map<string, string[]>;
}) {
  const showDataSources = Boolean(
    (sources && sources?.length > 0) ||
      (sourceToProductionSources && sourceToProductionSources.size > 0)
  );

  if (showDataSources == false) {
    return null;
  }

  return (
    <div className="flex flex-col py-2">
      <div className="flex flex-row pb-2">
        <div className="mr-1">{icon}</div>
        <div className="text-md font-semibold">{title}</div>
      </div>
      {sources && SourcesWithoutLegends({ sources: sources })}
      {sourceToProductionSources &&
        SourcesWithLegends({ sourceToProductionSources: sourceToProductionSources })}
    </div>
  );
}

function SourcesWithoutLegends({ sources }: { sources: string[] }) {
  return (
    <div className="flex flex-col gap-2 pl-5">
      {sources.map((source, index) => (
        <div key={index}>
          <Source source={source} />
        </div>
      ))}
    </div>
  );
}

function SourcesWithLegends({
  sourceToProductionSources,
}: {
  sourceToProductionSources: Map<string, string[]>;
}) {
  return (
    <div className="flex flex-col gap-1 pl-5">
      {[...sourceToProductionSources.keys()].sort().map((source, index) => (
        <p key={index}>
          <Source source={source} />
          <span className="inline-flex translate-y-1 gap-1 pl-1.5">
            {sourceToProductionSources.get(source)?.map((productionSource, index) => (
              <span key={index} className="self-center object-center text-xs">
                <ProductionSourceLegend
                  electricityType={productionSource as ElectricityModeType}
                />
              </span>
            ))}
          </span>
        </p>
      ))}
    </div>
  );
}

function Source({ source }: { source: string }) {
  const link = extractLinkFromSource(source, sourceLinkMapping);
  if (link) {
    return <Link href={link} linkText={source} />;
  }

  return <span>{source}</span>;
}
