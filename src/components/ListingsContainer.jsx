import { ListingCard } from "./ListingCard"


export const ListingsContainer = ({ listingsToDisplay, tagMap, fetchListings, isAdminPage, triggerRefresh }) => {
    return <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {listingsToDisplay.map((listing, key) => 
                    <ListingCard listing={listing} key={key} 
                                 tags={(tagMap[listing.id] || [])}
                                 isAdminPage={isAdminPage}
                                 triggerRefresh={triggerRefresh}
                    />
                )}
            </div>
        </>
    
}