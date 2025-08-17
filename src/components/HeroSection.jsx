import { ArrowDown } from "lucide-react"

export const HeroSection = () => {
    return <section id="hero" className="relative min-h-screen flex flex-col items-center justify-center px-4">
        <div className="container max-w-4xl mx-auto text-center z-10">
            <div className="space-y-6">
                <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
                    <span className="opacity-0 animate-fade-in">Hi,</span>
                    <span className="text-gradient opacity-0 animate-fade-in-delay-1">{" "}I'm</span>
                    <span className="text-gradient ml-2 opacity-0 animate-fade-in-delay-2">
                        {" "}Plasticmeth
                        <span className="text-primary">enjoyer</span>
                    </span>
                </h1>

                <p className="text-lg md:text-xl text-muted-foreground max-2-2xl mx-auto opacity:0 animate-fade-in-delay-3">
                    A fellow gunpla addict.
                </p>

                <p className="text-md md:text-lg text-muted-foreground max-2-2xl mx-auto opacity:0 animate-fade-in-delay-4">
                    This is my personal website where I share my collection of Gundam kits and accessories.
                    You'll be able to find cheaper prices here than on Carousell, but only if you initiate
                    the deal on <a href="https://t.me/plasticmethenjoyer" target="_blank" rel="noopener noreferrer" className="text-primary underline">Telegram</a>.
                    <p>
                        As I've recently launched my <a href="https://t.me/plasticmethenjoyergroup" target="_blank" rel="noopener noreferrer" className="text-primary underline">Telegram channel</a>,
                        I'll be having some special offers exclusively available there. Guaranteed best market price in Singapore.
                    </p>
                </p>

                <div>
                    <a href="#listings" className="cosmic-button opacity-0 animate-fade-in-delay-4">
                        View Listings
                    </a>
                </div>
            </div>
        </div>

        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex flex-col items-center animate-bounce">
            <span className="text-sm text-muted-foreground mb-2"> Scroll </span>
            <ArrowDown className="h-5 w-5 text-primary" />
        </div>
    </section>
}