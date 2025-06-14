import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";
import { useState, useEffect } from "react";
import { LogoutButton } from "./LogoutButton";
import { useNavigate } from "react-router-dom";
const navItems = [
    {name: "Home", href: "#hero"},
    {name: "About", href: "#about"},
    {name: "Listings", href: "#listings"},
    {name: "Contact", href: "#contact"},
    {name: "FAQ", href: "#faq"},
];

const navHeight = 10;

export const Navbar = ({ isSignedIn, isAdmin }) => {
    console.log("isSignedIn prop:", isSignedIn);
    console.log("isAdmin prop:", isAdmin);
    const [isScrolled, setIsScrolled] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.screenY > navHeight);
        }
        
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    const AdminButton = () => {
        const navigate = useNavigate();

        const navigateAdmin = () => {
            navigate("/secret-admin-page");
        }

        return (
            <button onClick={navigateAdmin} className="cosmic-button ml-4">
                Admin Page
            </button>
        );
    };

    return <nav className=
                    {cn("fixed w-full z-40 transition-all duration-300",
                        isScrolled ? "py-3 bg-background/80 backdrop-blur-md shadow-xs"
                                   : "py-5")
                    }
            >
                <div className="container flex items-center justify-between">
                    <a className="text-xl font-bold text-primary flex items-center" href="#hero">
                        <span className="relative z-10">
                            <span className="text-glow text-foreground"> Plasticmeth</span>enjoyer
                        </span>
                    </a>

                    {/* desktop nav */}
                    <div className="hidden md:flex space-x-8">
                        {navItems.map((item, key) => (
                            <a href={item.href} key={key} 
                                className="text-foreground/80 hover:text-primary transition-colors duration-300">
                                {item.name}
                            </a>
                        ))}
                        
                            {isSignedIn ? <LogoutButton />
                                        : <a href={"#login"} className="cosmic-button">Log In</a>
                            }
                            {isAdmin && <AdminButton />}
                    </div>

                    {/* mobile nav */}

                    <button onClick={() => setIsMenuOpen(menuStatus => !menuStatus)}
                        className="md:hidden p-2 text-foreground z-50"
                        aria-label={isMenuOpen ? "Close Menu" : "Open Menu"}
                    > 
                        {isMenuOpen ? <X size={24} /> : <Menu size={24} />} 
                    </button>

                    <div className={cn(
                            "fixed inset-0 bg-background/95 backdrop-blur-md z-40 flex flex-col items-center justify-center",
                            "transition-all duration-300 md:hidden",
                            isMenuOpen ? "opacity-100 pointer-events-auto"
                                       : "opacity-0 pointer-events-none" // opacity 0 to make invis
                                      )
                                    }
                    >
                        
                        <div className="flex flex-col space-y-8 text-xl">
                            {navItems.map((item, key) => (
                                <a href={item.href} 
                                   key={key} 
                                   className="text-foreground/80 hover:text-primary transition-colors duration-300"
                                   onClick={() => setIsMenuOpen(false)}>
                                    {item.name}
                                </a>
                            ))}
                            {isSignedIn ? <LogoutButton />
                                        : <a href={"#login"} className="cosmic-button">Log In</a>
                            }
                            {isAdmin && <AdminButton />}
                        </div>
                    </div>
                </div>
    </nav>
}