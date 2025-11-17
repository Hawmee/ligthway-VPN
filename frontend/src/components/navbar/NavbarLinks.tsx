import { type JSX, type ReactNode, type Ref } from 'react'
import { NavLink } from 'react-router-dom';

interface propsType{
    children?: ReactNode;
}

interface propsLinkType{
    icon?: any;
    text?: string;
    href?: any; 
}

export function NavBarLinksContainer({children} : propsType) : JSX.Element {
  return (
    <>
        <ul>
            {children}
        </ul>
    </>
  )
}

export function NavBarLinksContent({icon , text , href} : propsLinkType ) : JSX.Element {
    return(
        <>
            <li>
                <NavLink
                    className={({ isActive }) => `
                    flex items-center py-2 px-3 my-1 font-medium rounded-md cursor-pointer transition-colors text-sm
                    ${
                        isActive
                            ? "bg-gray-100 text-blue-400"
                            : "hover:bg-gray-200 text-gray-500 "
                    }
                `}
                    to={href}
                    end
                >
                    {icon}
                    <span className=" ml-3">{text}</span>
                </NavLink>
            </li>
        </>
    )
}
