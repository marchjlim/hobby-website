import { useState } from "react";
import { EditListingButton } from "./EditListingButton"
import { EditListingForm } from "./EditListingForm";
import { Check, CheckCircle, Clock } from "lucide-react";
import { DeleteListingButton } from "./DeleteListingButton";


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

    const PriceTag = ({ price, platform, currency = "SGD", className = "" }) => {
        return (
            <div
            className={`inline-flex items-center px-3 py-1 rounded-full bg-primary/80 text-white text-sm font-semibold shadow-sm ${className}`}
            >
            {platform}: 
            ${price}
            </div>
        );
    };

    const CarousellLink = ({ link }) => {
        return (
            <a href={link} 
               target="_blank"
               title="View listing on Carousell"
               className="text-muted-foreground hover:text-primary transition-colors">
                    <img src="icons/Carousell-logo-square.png" className="h-6 w-6 rounded" />
            </a>
        );
    }

    const TelegramLink = ({ link }) => {
        return (
            <a href={link} 
               target="_blank"
               title="Contact seller on Telegram"
               className="text-muted-foreground hover:text-primary transition-colors">
                    <img src="icons/Telegram-icon.png" className="h-6 w-6 rounded" />
            </a>
        );
    }

    const PreorderBadge = ({ className = "", arrival, deposit }) => {
        return (
            <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500 text-white text-sm font-semibold shadow-md ${className}`}
            >
            <Clock size={16} className="stroke-white" />
            Preorder, arrival in {arrival}. Deposit: ${deposit}
            </div>
        );
    };

    const InStockBadge = ({ className = "" }) => {
        return (
            <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500 text-white text-sm font-semibold shadow-md ${className}`}
            >
            <CheckCircle size={16} className="stroke-white" />
            In Stock
            </div>
        );
    };

    const RestockingBadge = ({ className = "" }) => {
        return (
            <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500 text-white text-sm font-semibold shadow-md ${className}`}
            >
            <Clock size={16} className="stroke-white" />
            Restocking
            </div>
        );
    };



    return <div key={key} className="bg-card p-6 rounded-lg shadow-xs card-hover"> 
                { isEditing ? (<EditListingForm listing={listing} initialListingTags={tags}
                                                onListingEdited={async () => {
                                                    triggerRefresh();
                                                    setIsEditing(false);
                                                }}
                                                onCancel={() => setIsEditing(false)}
                                />
                              )

                            : (<>
                            <div className="flex flex-col items-start">
                                <div className="text-left gap-4 flex justify-between items-start w-full h-10">
                                    <h3 className="w-full overflow-x-hidden font-semibold text-md md:text-lg break-words whitespace-normal"> {listing.name} </h3>
                                    <div className="flex flex-row gap-2">
                                        {isSelectable && (isSelected ? <UnselectButton /> : <SelectButton />)}
                                        {isModifiable && <EditListingButton listing={listing} onEdited={() => setIsEditing(true)} />}
                                        {isModifiable && <DeleteListingButton listing={listing} onDeleted={triggerRefresh} />}
                                    </div>
                                </div>
                
                            </div>

                                    
                                
                                <div className="flex flex-col gap-2 items-start mt-10">
                                    <img src={listing.image_url} 
                                        className="w-70 h-70 object-contain transition-transform duration-500 group-hover:scale-110" 
                                     />
                                    <div className="flex w-full justify-between">
                                        <PriceTag price={listing.carousell_price} platform="Carousell" />
                                        <CarousellLink link={listing.link} />    
                                    </div>
                                    
                                    <div className="flex w-full justify-between">
                                        <PriceTag price={listing.price} platform="Telegram" />
                                        <TelegramLink link={listing.telegram_link} />    
                                    </div>
                                    
                                    {listing.is_preorder ? <PreorderBadge arrival={listing.arrival_date} deposit={listing.deposit} /> 
                                                         : listing.is_restocking
                                                         ? <RestockingBadge /> 
                                                         : <InStockBadge />}
                                </div>
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