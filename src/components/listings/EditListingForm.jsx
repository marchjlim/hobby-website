import { useState } from "react"
import { authenticatedFetch } from "@/lib/authenticated-fetch";
import { WithContext as ReactTagInput } from 'react-tag-input';
import { useToast } from "@/hooks/use-toast";
import { Trash, X } from 'lucide-react';

export const EditListingForm = ({ listing, initialListingTags, onListingEdited, onCancel }) => {
    // convert each tag to the structure of ReactTagInput
    let formattedInitialListingTags = initialListingTags.map(tag => ({ id: tag, text: tag }));

    const [formData, setFormData] = useState({
        listingName: listing.name,
        listingDescription: listing.description ?? "",
        listingImg: listing.image_url,
        listingTags: formattedInitialListingTags,
        listingPrice: listing.price,
        listingLink: listing.link,
        listingIsPreorder: listing.is_preorder,
        listingDeposit: listing.deposit,
        listingArrival: listing.arrival_date,
        listingCarousellPrice: listing.carousell_price,
        listingIsRestocking: listing.is_restocking,
        listingIsActive: listing.is_active ?? true,
        listingTelegramLink: listing.telegram_link,
    });

    const [allTags, setAllTags] = useState(formattedInitialListingTags);
    const [updatedListingImage, setUpdatedListingImage] = useState(null);

    const { toast } = useToast();

    const handleFileChange = (event) => {
        // store file into a state
        if (event.target.files && event.target.files.length > 0) {
            setUpdatedListingImage(event.target.files[0]);
        }
    };

    const handleUpdate = async (event) => {
        event.preventDefault();
        const requestBody = new FormData();
        requestBody.append("payload", JSON.stringify({
            name: formData.listingName,
            image_url: formData.listingImg,
            description: formData.listingDescription,
            price: Number(formData.listingPrice),
            link: formData.listingLink,
            is_preorder: formData.listingIsPreorder,
            deposit: formData.listingDeposit === null ? null : Number(formData.listingDeposit),
            arrival_date: formData.listingArrival,
            is_restocking: formData.listingIsRestocking,
            is_active: formData.listingIsActive,
            carousell_price: formData.listingCarousellPrice === null ? null : Number(formData.listingCarousellPrice),
            telegram_link: formData.listingTelegramLink,
            tags: allTags.map(tag => tag.text),
        }));
        if (updatedListingImage) {
            requestBody.append("image", updatedListingImage);
        }

        const response = await authenticatedFetch(`/api/listings/${listing.id}`, {
            method: "PATCH",
            body: requestBody,
        });
        if (!response.ok) {
            console.error("Error updating listing", response.status);
            return;
        }

        onListingEdited();
    };

    const addTag = (tag) => {
        // do not allow adding duplicate if tags already selected.
        if (!allTags.some(t => t.text.toLowerCase() === tag.text.toLowerCase())) {
            setAllTags([...allTags, tag]);
        } else {
            // duplicate tag
            setTimeout(() => {
                toast({
                    title: "Duplicate tag detected",
                    description: "Please ensure all tags for a listing are unique",
                })
            }, 1000);
        }
    }

    const deleteTag = (idx) => {
        setAllTags(allTags.filter((tag, index) => idx !== index));
    }

    const deleteAllTags = () => {
        setAllTags([]);
    }

    const PreorderCheckbox = () => {
        return <>
            <label className="flex items-center gap-2">
                <span className="text-sm font-medium">Preorder item?</span>
                <div className="relative">
                    <input
                    type="checkbox"
                    checked={formData.listingIsPreorder}
                    onChange={(e) =>
                        setFormData((prev) => ({
                        ...prev,
                        listingIsPreorder: e.target.checked,
                        }))
                    }
                    className="peer sr-only"
                    />
                    <div className="w-10 h-5 bg-gray-300 rounded-full relative peer-checked:bg-green-500 transition" />
                    <div className="absolute left-1 top-1 w-3 h-3 bg-white rounded-full peer-checked:translate-x-5 transition-transform" />
                </div>
                

            </label>
        </>
    };

    const RestockingCheckbox = () => {
        return <>
            <label className="flex items-center gap-2">
                <span className="text-sm font-medium">Restocking item?</span>
                <div className="relative">
                    <input
                    type="checkbox"
                    checked={formData.listingIsRestocking}
                    onChange={(e) =>
                        setFormData((prev) => ({
                        ...prev,
                        listingIsRestocking: e.target.checked,
                        }))
                    }
                    className="peer sr-only"
                    />
                    <div className="w-10 h-5 bg-gray-300 rounded-full relative peer-checked:bg-green-500 transition" />
                    <div className="absolute left-1 top-1 w-3 h-3 bg-white rounded-full peer-checked:translate-x-5 transition-transform" />
                </div>
            </label>
        </>
    };


    

    return (
        <form onSubmit={handleUpdate} className="flex flex-col w-full space-y-4">
            <div className="flex flex-col mb-4 gap-2">
                <div className="relative w-full text-center">
                    <div className="text-secondary text-xl font-semibold">Listing name</div>
                    <button type="button" className="absolute top-0 right-0 group" onClick={onCancel}>
                        <X className="text-red-400"/>
                        <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                        bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                                            Cancel edit
                        </span>
                    </button>
                </div>
                
                <input name="name" 
                       type="text" 
                       placeholder="Listing name" 
                       required
                       className="w-full px-3 py-1 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingName} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingName: event.target.value }));
                       }} />

                <div className="space-y-2">
                    <div className="flex items-end justify-between gap-4">
                        <label htmlFor="edit-listing-description" className="font-medium text-secondary">
                            Description
                        </label>
                        <span className="text-xs tabular-nums text-muted-foreground" aria-live="polite">
                            {formData.listingDescription.length} / 1000
                        </span>
                    </div>
                    <textarea
                        id="edit-listing-description"
                        name="description"
                        placeholder="Describe the kit, condition, included accessories, and anything buyers should know?"
                        maxLength={1000}
                        rows={5}
                        className="w-full resize-y rounded-xl border border-input bg-primary/[0.06] px-4 py-3 leading-relaxed shadow-inner transition-colors placeholder:text-muted-foreground/60 hover:border-primary/50 hover:bg-primary/[0.08] focus:border-primary focus:outline-hidden focus:ring-2 focus:ring-primary/30"
                        value={formData.listingDescription}
                        onChange={(event) => setFormData((prev) => ({...prev, listingDescription: event.target.value}))}
                    />
                </div>

                <div className="flex flex-row gap-2">
                    <div className="flex flex-col">
                        <span className="text-center">Price</span>
                        <input name="price" 
                        type="number" 
                        placeholder="0" 
                        required
                        className="w-full px-3 py-1 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                        value={formData.listingPrice} 
                        onChange={(event) => {
                            setFormData((prev) => ({...prev, listingPrice: event.target.value }));
                        }} />
                    </div>
                    
                    <div className="flex flex-col">
                        <span className="text-center">Carousell Price</span>
                        <input name="carousellPrice" 
                        type="number" 
                        placeholder="0" 
                        required
                        className="w-full px-3 py-1 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                        value={formData.listingCarousellPrice} 
                        onChange={(event) => {
                            setFormData((prev) => ({...prev, listingCarousellPrice: event.target.value }));
                        }} />
                    </div>
                </div>
                
                <label className="flex items-center gap-2">
                    <input
                        type="checkbox"
                        checked={formData.listingIsActive}
                        onChange={(event) => setFormData((prev) => ({
                            ...prev,
                            listingIsActive: event.target.checked,
                        }))}
                        className="h-4 w-4 accent-primary"
                    />
                    <span className="text-sm font-medium">Active listing</span>
                </label>
                <RestockingCheckbox />
                <PreorderCheckbox />
                {formData.listingIsPreorder && <input
                                                name="deposit"
                                                type="number"
                                                placeholder="Deposit amount"
                                                required
                                                className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                                                value={formData.listingDeposit}
                                                onChange={(event) => {
                                                setFormData((prev) => ({
                                                    ...prev,
                                                    listingDeposit: event.target.value,
                                                }));
                                                }}
                                            />
                }
                {formData.listingIsPreorder && <input
                                                    name="arrival"
                                                    type="text"
                                                    placeholder="Arrival date"
                                                    required
                                                    className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                                                    value={formData.listingArrival}
                                                    onChange={(event) => {
                                                    setFormData((prev) => ({
                                                        ...prev,
                                                        listingArrival: event.target.value,
                                                    }));
                                                    }}
                                                />
                }

                <input name="link" 
                       type="url" 
                       placeholder="https://..." 
                       required
                       className="w-full px-3 py-1 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingLink} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingLink: event.target.value }));
                       }} />

                <input name="telegramLink"
                       type="url"
                       placeholder="https://t.me/..."
                       required
                       className="w-full px-3 py-1 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingTelegramLink}
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingTelegramLink: event.target.value }));
                       }} />

                
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Listing tags:
                </span>
                <div className="flex flex-row gap-2 w-full px-4 py-3 overflow-x-auto rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary">
                    {allTags.map((tag) => (
                        <span className="tag rounded-full border-1">
                            {tag.text}
                        </span>
                    ))}
                </div>
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Add new tag:
                </span>
                <div className="flex w-full px-2 py-2 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary">
                    <ReactTagInput
                        tags={allTags}
                        handleDelete={deleteTag}
                        handleAddition={addTag}
                        inputFieldPosition="bottom"
                        placeholder="Create new tag"
                        classNames={{
                            tag: 'border-1 rounded-full px-1 mr-2',
                            tagInputField: 'w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary',
                            tagInput: 'py-2',
                            remove: 'px-1'
                        }}
                    />
                </div>
                
                <span className="flex justify-between gap-2">
                    <label className="cosmic-button">
                        {updatedListingImage ? updatedListingImage.name : "Upload New Image"}
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            className="hidden"
                        />
                    </label>
                    <button type="button" className="flex flex-row px-3 py-2 font-medium rounded-full bg-primary"
                            onClick={deleteAllTags}> 
                        Delete all tags
                        <Trash />
                    </button>
                </span>
                
            </div>
            
            <button type="submit" className="cosmic-button">Update Listing</button>
        </form>
    )
}
