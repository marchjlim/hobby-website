import { useEffect, useState } from "react"
import { authenticatedFetch } from "@/lib/authenticated-fetch";
import { WithContext as ReactTagInput } from 'react-tag-input';
import { useToast } from "@/hooks/use-toast";
import { Trash } from 'lucide-react';

export const ListingForm = ({ onListingCreated }) => {
    const [formData, setFormData] = useState({
        listingName: "",
        listingDescription: "",
        listingImg: "",
        listingTags: [],
        listingPrice: null,
        carousellPrice: null,
        listingLink: "",
        listingIsPreorder: false,
        listingIsRestocking: false,
        listingIsActive: true,
        listingDeposit: null,   
        listingArrival: "",
        listingTelegramLink:"https://t.me/plasticmethenjoyer",
    });

    const [allTags, setAllTags] = useState([]);
    const [listingImage, setListingImage] = useState(null);
    const [isGeneratingDetails, setIsGeneratingDetails] = useState(false);
    const [generationError, setGenerationError] = useState("");
    const [pricingRationale, setPricingRationale] = useState("");
    const [pricingSuggestionId, setPricingSuggestionId] = useState(null);

    const { toast } = useToast();

    const fetchAllTags = async () => {
        const response = await fetch("/api/listings/tags");
        if (!response.ok) {
            console.error("Error fetching all tags: ", response.status);
            return;
        }
        const payload = await response.json();
        const tagData = payload.results ?? [];
        setAllTags(tagData.map(row => ({ id: row.name, text: row.name })));
    }

    useEffect(() => {
        fetchAllTags();
    }, []);

    const addPredefinedTag = (tag) => {
        // add into tags
        addTag(tag);
    }

    const handleFileChange = (event) => {
        setListingImage(event.target.files?.[0] ?? null);
        setGenerationError("");
        setPricingRationale("");
        setPricingSuggestionId(null);
    };

    const generateListingDetails = async () => {
        if (!listingImage) return;

        const body = new FormData();
        body.append("image", listingImage);
        setIsGeneratingDetails(true);
        setGenerationError("");
        try {
            const endpoint = "/api/ai/suggest-listing-details";
            const response = await authenticatedFetch(endpoint, {
                method: "POST",
                body,
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail ?? "Unable to generate suggestions");

            setFormData((current) => ({
                ...current,
                listingName: current.listingName || payload.name || "",
                listingDescription: current.listingDescription || payload.description || "",
                listingPrice: current.listingPrice ?? payload.suggested_price ?? null,
                carousellPrice: current.carousellPrice ?? payload.suggested_carousell_price ?? null,
            }));
            setPricingRationale(payload.pricing_rationale ?? "");
            setPricingSuggestionId(payload.pricing_suggestion_id ?? null);
            setTags((current) => {
                const existing = new Set(current.map((tag) => tag.text.toLowerCase()));
                return current.concat(
                    payload.tag_suggestions
                        .map(({ tag }) => ({ id: tag, text: tag }))
                        .filter((tag) => !existing.has(tag.text.toLowerCase()))
                );
            });
        } catch (error) {
            setGenerationError(`${error.message}. Try again.`);
        } finally {
            setIsGeneratingDetails(false);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        const requestBody = new FormData();
        requestBody.append("payload", JSON.stringify({
            name: formData.listingName,
            price: Number(formData.listingPrice),
            description: formData.listingDescription,
            link: formData.listingLink,
            is_preorder: formData.listingIsPreorder,
            deposit: formData.listingDeposit === null ? null : Number(formData.listingDeposit),
            arrival_date: formData.listingArrival,
            is_restocking: formData.listingIsRestocking,
            is_active: formData.listingIsActive,
            carousell_price: formData.carousellPrice === null ? null : Number(formData.carousellPrice),
            telegram_link: formData.listingTelegramLink,
            tags: tags.map(tag => tag.text),
            pricing_suggestion_id: pricingSuggestionId,
        }));
        if (listingImage) {
            requestBody.append("image", listingImage);
        }

        const response = await authenticatedFetch("/api/listings", {
            method: "POST",
            body: requestBody,
        });
        if (!response.ok) {
            console.error("Error adding listing", response.status);
            return;
        }



        setFormData({
            listingName:"",
            listingImg: "",
            listingDescription: "",
            listingTags: [],
            listingPrice: null,
            listingLink: "", 
            listingIsPreorder: false,
            listingDeposit: 0,
            listingArrival: "",
            carousellPrice: null,
            listingIsRestocking: false,
            listingIsActive: true,
            listingTelegramLink: "https://t.me/plasticmethenjoyer",
        });
        setTags([]);
        setListingImage(null);

        setPricingRationale("");
        setPricingSuggestionId(null);
        await fetchAllTags();
        await onListingCreated();

        toast({
                    title: "Listing created",
                    description: "Your listing has been successfully created",
                });
    };

    const [tags, setTags] = useState([]);

    const addTag = (tag) => {
        // do not allow adding duplicate if tags already selected.
        if (!tags.some(t => t.text.toLowerCase() === tag.text.toLowerCase())) {
            setTags([...tags, tag]);
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
        setTags(tags.filter((tag, index) => idx !== index));
    }

    const deleteAllTags = () => {
        setTags([]);
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
        <form onSubmit={handleSubmit} className="flex flex-col bg-card mx-auto px-100">
            <h3 className="text-3xl md:text-4xl font-bold text-center mb-4"> New Listing Details </h3>
            <div className="flex flex-col mb-4 gap-2">
                <span className="text-secondary text-2xl md:text-3xl font-semibold">Listing name</span>
                <input name="name" 
                       type="text" 
                       placeholder="Listing name" 
                       required
                       className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingName} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingName: event.target.value }));
                       }} />

                <div className="space-y-2">
                    <div className="flex items-end justify-between gap-4">
                        <label htmlFor="listing-description" className="text-secondary text-2xl md:text-3xl font-semibold">
                            Description
                        </label>
                        <span className="text-xs tabular-nums text-muted-foreground" aria-live="polite">
                            {formData.listingDescription.length} / 1000
                        </span>
                    </div>
                    <textarea
                        id="listing-description"
                        name="description"
                        placeholder="Describe the kit, condition, included accessories, and anything buyers should know?"
                        maxLength={1000}
                        rows={5}
                        className="w-full resize-y rounded-xl border border-input bg-primary/[0.06] px-4 py-3 leading-relaxed shadow-inner transition-colors placeholder:text-muted-foreground/60 hover:border-primary/50 hover:bg-primary/[0.08] focus:border-primary focus:outline-hidden focus:ring-2 focus:ring-primary/30"
                        value={formData.listingDescription}
                        onChange={(event) => setFormData((prev) => ({...prev, listingDescription: event.target.value}))}
                    />
                </div>

                <span className="text-secondary text-2xl md:text-3xl font-semibold">Price</span>
                <div className="flex flex-row gap-2">
                    <input name="price" 
                       type="number" 
                       placeholder="Price on website" 
                       required
                       className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingPrice} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingPrice: event.target.value }));
                       }} />
                
                    <input name="carousellPrice" 
                        type="number" 
                        placeholder="Price on Carousell" 
                        required
                        className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                        value={formData.carousellPrice} 
                        onChange={(event) => {
                            setFormData((prev) => ({...prev, carousellPrice: event.target.value }));
                        }} />
                </div>
                

                {pricingRationale && <p className="text-sm text-muted-foreground">{pricingRationale}</p>}
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
                
                <span className="text-secondary text-2xl md:text-3xl font-semibold">Link to carousell listing</span>
                <input name="link" 
                       type="url" 
                       placeholder="https://..." 
                       required
                       className="w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary"
                       value={formData.listingLink} 
                       onChange={(event) => {
                        setFormData((prev) => ({...prev, listingLink: event.target.value }));
                       }} />

                <span className="text-secondary text-2xl md:text-3xl font-semibold">
                    Choose some existing tags or add your own
                </span>
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Existing tags:
                </span>
                <div className="flex flex-row gap-2 w-full px-4 py-3 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary overflow-x-auto whitespace-nowrap">
                    {allTags.map((tag) => (
                        <button type="button"
                                className="tag rounded-full border-1" 
                                onClick={() => addPredefinedTag(tag)}>
                                    {tag.text}
                        </button>
                    ))}
                </div>
                <span className="text-secondary text-lg md:text-1xl font-semibold">
                        Selected tags:
                </span>
                <div className="flex w-full px-2 py-2 rounded-md border border-input bg-background focus:outline-hidden focus:ring-2 focus:ring-primary">
                    <ReactTagInput
                        tags={tags}
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
                        {listingImage ? listingImage.name : "Upload Image"}
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            className="hidden"
                        />
                    </label>
                    <button className="flex flex-row px-3 py-2 font-medium rounded-full bg-primary disabled:opacity-50"
                            type="button"
                            disabled={!listingImage || isGeneratingDetails}
                            onClick={generateListingDetails}>
                        {isGeneratingDetails ? "Generating details..." : "Generate listing details"}
                    </button>
                    <button className="flex flex-row px-3 py-2 font-medium rounded-full bg-primary"
                            type="button"
                            onClick={deleteAllTags}> 
                        Delete all tags
                        <Trash />
                    </button>
                </span>
                {generationError && <span className="text-red-500">{generationError}</span>}
                
            </div>
            
            <button type="submit" className="cosmic-button">Create Listing</button>
        </form>
    )
}
