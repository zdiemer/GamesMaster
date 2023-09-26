import { useRouter } from 'next/router'
import useSWR from "swr";
import { Game } from '../../components/game';
import Page from '../../components/page';
import Link from 'next/link'

export default function Games() {
  const router = useRouter()
  const { id } = router.query;
  console.log(`id: ${id}`);

  const fetcher = (...args) => fetch(...args).then((res) => res.json());
  console.log(`port: ${process.env.API_PORT}`);
  const { data: gameData, error, isLoading } = useSWR(!!id ? `/api/games/${id}` : null, fetcher);
  const { data: releaseData, error: error2, isLoading: isLoading2 } = useSWR(!!id ? `/api/games/${id}/releases` : null, fetcher);
  // const { data: purchaseData } = useSWR(!!id ? `/api/games/${id}/purchases` : null, fetcher);

  if (error || error2) return <div>Failed to fetch users.</div>;
  if (isLoading || isLoading2) return <h2>Loading...</h2>;

  let dlcStanza = undefined;
  if (gameData?.dlc.length > 0) {
    dlcStanza = (
      <div>
        <h2>DLC</h2>
        {gameData?.dlc?.map((game: any, index) => {
          return (
            <div key={index}><Game game={game} /></div>
          );
        })}
      </div>
    );
  }

  let collectionStanza = undefined;
  if (gameData?.collectees.length > 0) {
    collectionStanza = (
      <div>
        <h2>Collection Contents</h2>
        {gameData?.collectees?.map((game: any, index) => {
          return (
            <div key={index}><Game game={game} /></div>
          );
        })}
      </div>
    );
  }

  let developersStanza = undefined;
  if (gameData?.notable_developers.length > 0) {
    developersStanza = (
      <div>
        Developers:
        <ul>
          {gameData?.notable_developers?.map((developer: any, i) => {
            return (
              <li key={i}>{developer.role}: {developer.name}</li>
            );
          })}
        </ul>
      </div>
    );
  }

  const reviews = [];
  reviews.push(...releaseData?.results.flatMap((rls) => {
    let reviews = rls.reviews || [];
    return reviews.map(rev => {
      // If there's no platform, default to all from the parent.
      if (rev.platforms.length === 0) {
        rev.platforms = rls.platforms;
      }
      return rev;
    });
  }) || []);

  const purchases = [];
  purchases.push(...releaseData?.results.flatMap((rls) => {
    return rls.purchases || [];
  }) || []);


  return (
    <Page>
      <h1>{gameData?.title}</h1>
      {/* // TODO: exterkamp - use real art for the games. */}
      <img src={`/images/${gameData?.cover_art_uuid}`} height={200}></img>
      <div>
        <p>
          Franchise: <span>{gameData?.franchises.map((f, i) => {
            return (<Link key={i} href={`/franchises/${f.url_slug}`}>{f.name}</Link>);
          })}</span>
          <br />
          Genre(s): <span>{gameData?.genres.join(", ")}</span>
          <br />
          Developed by: <span>{gameData?.developers.map((d, i, arr) => {
            return (<span key={i}><Link href={`/companies/${d.url_slug}`}>{d.name}</Link>{i !== arr.length - 1 && <>, </>}</span>)
          })}</span>
        </p>
        {!!developersStanza ? developersStanza : ''}
      </div>
      <span>Releases:</span>
      <ul>
        {releaseData?.results.map((release: any, index) => {
          return (
            <li key={index}>Released {release.release_date} in {convertRegionToEmoji(release.region)} for {
              release.platforms.map((rls, i, arr) => {
                return (<span key={i}><Link href={`/platforms/${rls.url_slug}`}>{rls.name}</Link>{i !== arr.length - 1 && <>, </>}</span>)
              })} by {release.publishers.map((plat, i, arr) => {
                return (<span key={i}><Link href={`/companies/${plat.url_slug}`}>{plat.name}</Link></span>)
              })}</li>
          );
        })}
      </ul>

      {!!reviews.length && <span>Reviews:</span>}
      <ul>
        {reviews.map((rev, i) => {
          return (<li key={i}>{rev.rating} from {rev.reviewing_agency} on {rev.platforms.map((r, i, arr) => {
            return (<span key={i}><Link href={`/platforms/${r.url_slug}`}>{r.name}</Link>{i !== arr.length - 1 && <>, </>}</span>)
          })}{!!rev.notes && <><br />"{rev.notes}"</>}</li>);
        })}
      </ul>

      {!!purchases.length && <span>Purchase Records:</span>}
      <ul>
        {purchases.map((p, i) => {
          return (<li key={i}><div >purchased on {p.purchase_date} for ${p.purchase_price} on <Link href={`/platforms/${p.platform.url_slug}`}>{p.platform.name}</Link></div></li>);
        })}
      </ul>


      {!!dlcStanza ? dlcStanza : ''}
      {!!collectionStanza ? collectionStanza : ''}
      {/* 
      {purchaseData?.results.map((purchase: any, index) => {
        return (
          <div key={index}>purchased on {purchase.purchase_date} for ${purchase.purchase_price}</div>
        );
      })} */}
    </Page>)
}

function convertRegionToEmoji(region: string) {
  switch (region) {
    case "North America":
      return "🇺🇸"
    case "Europe, Africa, and Asia":
      return "🇪🇺"
    case "Worldwide":
      return "🌐"
    default:
      return "🏴"
  }
}