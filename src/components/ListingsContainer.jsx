import { ListingCard } from "./ListingCard"


export const ListingsContainer = ({ listingsToDisplay, tagMap, isModifiable, triggerRefresh,
                                    hasSelectableListings = false, onListingSelect, onListingUnselect,
                                    selectedListingIds }) => {
    return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {listingsToDisplay.map((listing, key) => 
                    <ListingCard listing={listing} key={key} 
                                 tags={(tagMap[listing.id] || [])}
                                 isModifiable={isModifiable}
                                 triggerRefresh={triggerRefresh}
                                 isSelectable={hasSelectableListings}
                                 onSelect={onListingSelect}
                                 onUnselect={onListingUnselect}
                                 selectedListingIds={selectedListingIds}
                    />
                )}
            </div>
    );
    
}