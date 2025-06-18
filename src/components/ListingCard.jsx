import { useState } from "react";
import { DeleteListingButton } from "./DeleteListingButton"
import { EditListingButton } from "./EditListingButton"
import { EditListingForm } from "./EditListingForm";


export const ListingCard = ({ listing, key, tags, isAdminPage, triggerRefresh }) => {
    const [isEditing, setIsEditing] = useState(false);

    return <div key={key} className="bg-card p-6 rounded-lg shadow-xs card-hover"> 
                { isEditing ? (<EditListingForm listing={listing} initialListingTags={tags}
                                          onListingEdited={async () => {
                                            triggerRefresh();
                                            setIsEditing(false);
                                          }}/>)
                            : (<>
                                <div className="text-left mb-4 h-14 flex justify-between items-center">
                                    <h3 className="font-semibold text-lg md:text-xl line-clamp-2"> {listing.name} </h3>
                                    <span className="flex flex-row gap-2">
                                        {isAdminPage && <EditListingButton listing={listing} onEdited={() => setIsEditing(true)} />}
                                        {isAdminPage && <DeleteListingButton listing={listing} onDeleted={triggerRefresh} />}
                                    </span>
                                    
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