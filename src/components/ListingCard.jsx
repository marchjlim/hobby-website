import { useState } from "react";
import { DeleteListingButton } from "./DeleteListingButton"
import { EditListingButton } from "./EditListingButton"
import { EditListingForm } from "./EditListingForm";
import { Check } from "lucide-react";


export const ListingCard = ({ listing, key, tags, isModifiable, triggerRefresh,
                              isSelectable = false, onSelect, onUnselect, selectedListingIds }) => {
    const [isEditing, setIsEditing] = useState(false);

    let isSelected = selectedListingIds?.includes(listing.id);

    const handleSelect = () => {
        onSelect(listing);
    }
    const handleUnselect = () => {
        onUnselect(listing);
    }

    const SelectButton = () => (
        <button
            onClick={handleSelect}
            className="w-6 h-6 rounded-full border-2 border-primary bg-transparent hover:bg-primary/30 transition"
            aria-label="Select listing"
        />
    );


    const UnselectButton = () => (
        <button
            onClick={handleUnselect}
            className="w-6 h-6 flex items-center justify-center rounded-full bg-primary border-2 border-primary text-white hover:bg-primary/80 transition"
            aria-label="Unselect listing"
        >
            <Check className="w-4 h-4" />
        </button>
    );



    return <div key={key} className="bg-card p-6 rounded-lg shadow-xs card-hover"> 
                { isEditing ? (<EditListingForm listing={listing} initialListingTags={tags}
                                          onListingEdited={async () => {
                                            triggerRefresh();
                                            setIsEditing(false);
                                          }}/>)
                            : (<>
                                <div className="text-left mb-4 h-14 flex justify-between items-start">
                                    <h3 className="font-semibold text-lg md:text-xl break-words whitespace-normal w-full"> {listing.name} </h3>
                                    <div className="flex flex-row gap-2">
                                        {isSelectable && (isSelected ? <UnselectButton /> : <SelectButton />)}
                                        {isModifiable && <EditListingButton listing={listing} onEdited={() => setIsEditing(true)} />}
                                        {isModifiable && <DeleteListingButton listing={listing} onDeleted={triggerRefresh} />}
                                    </div>
                                    
                                </div>
                                    
                                <img src={listing.image_url} 
                                        className="w-70 h-70 object-contain transition-transform duration-500 group-hover:scale-110" 
                                />
                                <div className="mt-4 flex flex-wrap">
                                    {/*specify empty array here for listings with no tags to appear.*/}
                                    {tags.map((tag) => (
                                        <span className="px-2 py-1">
                                            <span className="rounded-full border-1 px-1 bg-secondary text-foreground">{tag}</span>
                                        </span>
                                    ))}
                                </div>
                              </>)
                }
           </div>
}